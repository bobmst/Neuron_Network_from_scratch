import numpy as np
import pandas as pd
from layers import Layer

# import asyncio


np.random.seed(seed=42)

# ----------------------------------------------------------------
# Layers
class InputLayer(Layer):
    # Input: dataIn, an NxD matrix
    # Output: None
    def __init__(self, dataIn, z_score=True):
        super().__init__()
        self.meanX = dataIn.mean(axis=0)
        stdX = dataIn.std(axis=0, ddof=1)
        stdX[stdX == 0] = 1
        # set std to 1 if the std equals 0 to prevent division by zero
        self.stdX = stdX
        self.z_scored = z_score

    # Input: dataIn, an NxD matrix
    # Output: An NxD matrix
    def forward(self, dataIn):
        if self.z_scored:
            dataOut = (dataIn - self.meanX) / self.stdX
        else:
            dataOut = dataIn
        self.setPrevIn(dataIn)
        self.setPrevOut(dataOut)

        return dataOut

    def gradient(self):
        pass

    def backward(self, gradIn):
        pass

    def fit(self, dataIn):
        if self.z_scored:
            dataOut = (dataIn - self.meanX) / self.stdX
        else:
            dataOut = dataIn

        return dataOut


# def to_jacobian_tensor(z):
#     rows = z.shape[0]
#     cols = z.shape[1]
#     tensor = np.zeros((rows, cols, cols))
#     for shape, value in np.ndenumerate(z):
#         tensor[shape[0], shape[1], shape[1]] = value
#     return tensor


class LinearLayer(Layer):
    # Input: None
    # Output : None
    def __init__(self):
        super().__init__()

    def linear_derivative(self, z):
        return np.ones(z.shape)

    # Input: dataIn , an NxK matrix
    # Output : An NxK matrix
    def forward(self, dataIn):
        self.setPrevIn(dataIn)
        self.setPrevOut(dataIn)
        return dataIn

    # Input: None
    # Output: An N by (D by D) tensor
    def gradient(self):
        return self.linear_derivative(self.getPrevOut())

    def backward(self, gradIn):
        g = self.gradient()
        return np.multiply(gradIn, g)

    def fit(self, dataIn):
        return dataIn


class ReLuLayer(Layer):
    # Input: None
    # Output : None
    def __init__(self):
        super().__init__()

    def ReLu(self, x):
        return np.maximum(0, x)

    def relu_derivative(self, z):
        return np.where(z <= 0, 0, 1)

    # Input: dataIn , an NxK matrix
    # Output : An NxK matrix
    def forward(self, dataIn):
        self.setPrevIn(dataIn)
        Y = self.ReLu(dataIn)
        self.setPrevOut(Y)
        return Y

    # Input: None
    # Output: An N by (D by D) tensor
    def gradient(self):
        return self.relu_derivative(self.getPrevOut())

    def backward(self, gradIn):
        g = self.gradient()
        return np.multiply(gradIn, g)

    def fit(self, dataIn):
        Y = self.ReLu(dataIn)
        return Y


class LogisticSigmoidLayer(Layer):
    # Input: None
    # Output : None
    def init(self):
        super().__init__()

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def logistic_derivative(self, z):
        g = lambda x: 1 / (1 + np.exp(-x))
        return g(z) * (1 - g(z))

    # Input: dataIn , an NxK matrix
    # Output : An NxK matrix
    def forward(self, dataIn):
        self.setPrevIn(dataIn)
        Y = self.sigmoid(dataIn)
        self.setPrevOut(Y)
        return Y

    # Input: None
    # Output: An N by (D by D) tensor
    def gradient(self):
        return self.logistic_derivative(self.getPrevOut())

    def backward(self, gradIn):
        g = self.gradient()
        return np.multiply(gradIn, g)

    def fit(self, dataIn):
        Y = self.sigmoid(dataIn)
        return Y


class SoftmaxLayer(Layer):
    def _init_(self):
        super()._init_()

    def softmax(self, x):
        if len(x.shape) == 1:
            return np.exp(x - np.max(x)) / np.exp(x - np.max(x)).sum()
        elif x.shape[1] == 1:
            return np.exp(x - np.max(x)) / np.exp(x - np.max(x)).sum()
        else:
            row_max = np.max(x, axis=1, keepdims=True)
            return np.exp(x - row_max) / np.sum(
                np.exp(x - row_max), axis=1, keepdims=True
            )

    def forward(self, dataIn):
        self.setPrevIn(dataIn)
        dataOut = self.softmax(dataIn)
        self.setPrevOut(dataOut)
        return self.getPrevOut()

    def gradient(self):
        T = []
        for row in self.getPrevOut():
            grad = np.diag(row) - row[np.newaxis].T.dot(row[np.newaxis])
            T.append(grad)
        return np.array(T)

    def backward(self, gradIn):
        grand = self.gradient()
        return np.einsum("ijk,ik->ij", grand, gradIn)

    def fit(self, dataIn):
        dataOut = self.softmax(dataIn)
        return dataOut


class TanhLayer(Layer):
    # Input: None
    # Output : None
    def init(self):
        super().__init__()

    def tanh_derivative(self, z):
        return 1 - (np.tanh(z)) ** 2

    # Input: dataIn , an NxK matrix
    # Output : An NxK matrix
    def forward(self, dataIn):
        self.setPrevIn(dataIn)
        Y = np.tanh(dataIn)
        self.setPrevOut(Y)
        return Y

    # Input: None
    # Output: An N by (D by D) tensor
    def gradient(self):
        return self.tanh_derivative(self.getPrevOut())

    def backward(self, gradIn):
        g = self.gradient()
        return np.multiply(gradIn, g)

    def fit(self, dataIn):
        Y = np.tanh(dataIn)
        return Y


class FullyConnectedLayer(Layer):
    # Input: sizeIn, the number of features of data coming in
    # Input: sizeOut, the number of features for the data coming out .
    # Output : None
    def __init__(self, sizeIn, sizeOut):
        super().__init__()
        self.weight = np.random.uniform(low=-1e-4, high=1e-4, size=(sizeIn, sizeOut))
        self.bias = np.random.uniform(low=-1e-4, high=1e-4, size=(sizeOut,))

        self.s_w = np.zeros((sizeIn, sizeOut))
        self.r_w = np.zeros((sizeIn, sizeOut))
        self.s_b = np.zeros((sizeOut,))
        self.r_b = np.zeros((sizeOut,))
        # self.s_w_prev = np.zeros((size))

    # Input: None
    # Output : The sizeIn x size Out weight matrix .
    def getWeights(self):
        return self.weight

    # Input: The sizeIn x size Out weight matrix .
    # Output : None
    def setWeights(self, weights):
        self.weight = weights

    # Input: The 1 x size Out biasvector
    # Output : None
    def getBiases(self):
        return self.bias

    # Input:None
    # Output : The 1 x size Outbiasevector
    def setBiases(self, biases):
        self.bias = biases

    # Input: dataIn , an NxD datamatrix
    # Output : An NxK datamatrix
    def forward(self, dataIn):
        self.setPrevIn(dataIn)
        Y = (np.dot(dataIn, self.weight) + self.bias).astype(np.float32)
        self.setPrevOut(Y)
        return Y

    # Input: None
    # Output: An NxD matrix
    def gradient(self):
        return self.weight.T

    def backward(self, gradIn):
        g = self.gradient()
        newgrad = gradIn @ g
        return newgrad.astype(np.float32)

    def fit(self, dataIn):
        Y = (np.dot(dataIn, self.weight) + self.bias).astype(np.float32)
        return Y

    def updateWeights(self, gradIn, eta=0.0001):
        # print(gradIn.shape)
        dJdb = np.sum(gradIn, axis=0) / gradIn.shape[0]
        dJdW = (self.getPrevIn().T @ gradIn) / gradIn.shape[0]

        self.weight -= eta * dJdW
        self.bias -= eta * dJdb

    def updateWeightsAdam(
        self,
        gradIn,
        t,
        eta=0.0001,
        rho1=0.9,
        rho2=0.999,
        epsilon=10e-8,
    ):
        t = t + 1
        dJdb = np.sum(gradIn, axis=0) / gradIn.shape[0]
        dJdW = (self.getPrevIn().T @ gradIn) / gradIn.shape[0]

        # update s and r
        # weight
        self.s_w = rho1 * self.s_w + (1 - rho1) * dJdW
        self.r_w = rho2 * self.r_w + (1 - rho2) * (np.multiply(dJdW, dJdW))

        # bias
        self.s_b = rho1 * self.s_b + (1 - rho1) * dJdb
        self.r_b = rho2 * self.r_b + (1 - rho2) * (np.multiply(dJdb, dJdb))

        # update weight and bias according to Adam algorithm.
        # print(self.s_w)
        s_w_hat = self.s_w / (1 - rho1**t)
        r_w_hat = self.r_w / (1 - rho2**t)

        s_b_hat = self.s_b / (1 - rho1**t)
        r_b_hat = self.r_b / (1 - rho2**t)

        delta_w = eta * s_w_hat / (np.sqrt(r_w_hat) + epsilon)
        delta_b = eta * r_b_hat / (np.sqrt(r_b_hat) + epsilon)

        self.weight -= delta_w
        self.bias -= delta_b


# ----------------------------------------------------------------
# Covolution Layer
class ConvolutionLayer(Layer):
    def __init__(self, kernel_num, kernel_size):
        super().__init__()
        self.kernel_num = kernel_num
        self.kernel_size = kernel_size
        # divide by to kernel_size**2 reduce the variance of our initial values
        self.kernels = (
            np.random.randn(kernel_num, kernel_size, kernel_size) / (kernel_size**2)
        ).astype(np.float32)

    def getKernels(self):
        return self.kernels

    def setKernels(self, kernels):
        self.kernels = kernels.astype(np.float32)
        self.kernel_num = kernels.shape[0]
        self.kernel_size = kernels.shape[1]

    def iterate_regions(self, image, region_size):
        h, w = image.shape

        for i in range(h - region_size + 1):
            for j in range(w - region_size + 1):
                im_region = image[i : (i + region_size), j : (j + region_size)]
                yield im_region, i, j

    def forward(self, dataIn):
        self.setPrevIn(dataIn)

        o, h, w = dataIn.shape
        pad_size = int(np.ceil(self.kernel_size / 2))
        output = np.zeros(
            (
                o,
                h - pad_size,
                w - pad_size,
            )
        )

        for row in range(o):
            for im_region, i, j in self.iterate_regions(dataIn[row], self.kernel_size):
                # print(row)
                # print(im_region, i, j, "\n")
                output[row, i, j] = np.sum(im_region * self.kernels)

        self.setPrevOut(output)
        return output

    def gradient(self):
        pass

    def updateKernels(self, gradIn, eta=0.001):
        prevIn = self.getPrevIn()
        o, h, w = prevIn.shape

        # gradOut = np.zeros(
        #     (
        #         o,
        #         h - gradIn.shape[1] + 1,
        #         w - gradIn.shape[1] + 1,
        #     )
        # )

        # gradOut = np.zeros(
        #     self.kernels.size
        # )
        # print("Grade Out Shape", gradOut.shape)

        for row in range(o):
            for im_region, i, j in self.iterate_regions(prevIn[row], gradIn.shape[1]):
                # print(gradIn.shape[1])
                # print("!!!", im_region.shape)
                # # print(row)
                # print(i, j, "\n")
                # print(im_region, i, j, "\n")
                # gradOut[row, i, j] = np.sum(im_region * gradIn[row])
                dJdK = np.sum(im_region * gradIn[row])
                self.kernels -= eta * dJdK * (1 / o)

            # self.kernels -= eta * gradOut[row]

        # for row in range(o):
        #     print("!!", prevIn[row].shape)
        #     print(gradIn.shape)
        #     for im_region, i, j in self.iterate_regions(prevIn[row], gradIn.shape[1]):
        #         print("!!!", im_region.shape)
        #         print(im_region, i, j, "\n")
        #         print(gradIn[row].shape)
        #         gradOut[row, i, j] = np.sum(im_region * gradIn[row])

        #     self.kernels -= eta * gradOut[row]

    def backward(self, gradIn, eta=0.01):

        prevIn = self.getPrevIn()
        o, h, w = prevIn.shape

        gradOut = np.zeros(
            (
                o,
                h,
                w,
            )
        )

        pad_size = int(np.ceil(self.kernel_size / 2))
        for row in range(o):
            new_img = np.pad(
                gradIn[row], ((pad_size, pad_size), (pad_size, pad_size)), "constant"
            )
            # print("!new_img_shape", new_img.shape)
            # print("!", new_img)

            for im_region, i, j in self.iterate_regions(new_img, self.kernel_size):
                # print(row)
                # print(im_region, i, j, "\n")
                gradOut[row, i, j] = np.sum(im_region * self.kernels.T)

        # self.learn(gradIn, eta)

        return gradOut

    def fit(self, dataIn):

        o, h, w = dataIn.shape
        pad_size = int(np.ceil(self.kernel_size / 2))
        output = np.zeros(
            (
                o,
                h - pad_size,
                w - pad_size,
            )
        )

        for row in range(o):
            for im_region, i, j in self.iterate_regions(dataIn[row], self.kernel_size):
                # print(row)
                # print(im_region, i, j, "\n")
                output[row, i, j] = np.sum(im_region * self.kernels)

        return output


# Max pooling
class MaxPoolingLayer(Layer):
    def __init__(self, stride):
        super().__init__()
        self.stride = stride

    def iterate_regions(self, image):
        h, w = image.shape
        new_h = h // self.stride
        new_w = w // self.stride
        for i in range(new_h):
            for j in range(new_w):
                im_region = image[
                    (i * self.stride) : (i * self.stride + self.stride),
                    (j * self.stride) : (j * self.stride + self.stride),
                ]
                yield im_region, i, j

    def forward(self, dataIn):
        self.setPrevIn(dataIn)
        o, h, w = dataIn.shape
        dataOut = np.zeros((o, h // self.stride, w // self.stride))
        for row in range(o):
            for im_region, i, j in self.iterate_regions(dataIn[row]):
                # print(row)
                # print(im_region, i, j, "\n")
                dataOut[row, i, j] = np.amax(im_region, axis=(0, 1))
        self.setPrevOut(dataOut)
        return dataOut

    def gradient(self):
        pass

    def backward(self, gradIn):
        prevIn = self.getPrevIn()
        gradOut = np.zeros(prevIn.shape)

        for row in range(prevIn.shape[0]):
            for im_region, i, j in self.iterate_regions(prevIn[row]):
                # print(row)
                # print(im_region, i, j, "\n")
                h, w = im_region.shape
                amax = np.amax(im_region, axis=(0, 1))
                # print(amax, "\n")

                for h2 in range(h):
                    for w2 in range(w):
                        # If this pixel was the max value, copy the gradient to it.
                        if im_region[h2, w2] == amax:
                            gradOut[
                                row, i * self.stride + h2, j * self.stride + w2
                            ] = gradIn[row, i, j]

        return gradOut

    def fit(self, dataIn):
        o, h, w = dataIn.shape
        dataOut = np.zeros((o, h // self.stride, w // self.stride))
        for row in range(o):
            for im_region, i, j in self.iterate_regions(dataIn[row]):
                dataOut[row, i, j] = np.amax(im_region, axis=(0, 1))
        return dataOut


# Avg pooling

# L2 pooling

# Flatten
class FlattenLayer(Layer):
    def __init__(self):
        super().__init__()

    # Input: dataIn , an NxK matrix
    # Output : An NxK matrix
    def forward(self, dataIn):
        self.setPrevIn(dataIn)

        Y = dataIn.reshape(
            (dataIn.shape[0], dataIn.shape[1] * dataIn.shape[2]), order="F"
        )

        self.setPrevOut(Y)
        return Y

    def gradient(self):
        pass

    def backward(self, gradIn):
        prevIn = self.getPrevIn()
        return gradIn.reshape(prevIn.shape, order="F")

    def fit(self, dataIn):
        Y = dataIn.reshape(
            (dataIn.shape[0], dataIn.shape[1] * dataIn.shape[2]), order="F"
        )
        return Y


# ----------------------------------------------------------------
# Evaluations
class SquaredError:
    def eval(self, Y, Yhat):
        return np.mean((Y - Yhat) * (Y - Yhat)).astype(np.float32)

    def gradient(self, Y, Yhat):
        return -2 * (Y - Yhat).astype(np.float32)


class LogLoss:
    def eval(self, Y, Yhat, epsilon=1e-7):
        return np.mean(
            -(Y * np.log(Yhat + epsilon) + (1 - Y) * np.log(1 - Yhat + epsilon)).astype(
                np.float32
            )
        )

    def gradient(self, Y, Yhat, epsilon=1e-7):
        return -(Y - Yhat) / (Yhat * (1 - Yhat) + epsilon).astype(np.float32)


class CrossEntropy:
    def eval(self, Y, Yhat, epsilon=1e-7):
        return -np.mean(Y * np.log(Yhat + epsilon)).astype(np.float32)

    def gradient(self, Y, Yhat, epsilon=1e-7):
        return -(Y / (Yhat + epsilon)).astype(np.float32)
