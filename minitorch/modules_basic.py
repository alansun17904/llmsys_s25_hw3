"""
For additional transformer related

Sequential
Embedding

"""
import numpy as np

from .module import Module, Parameter
from .tensor_functions import (zeros, ones, rand, tensor, tensor_from_numpy, zeros_tensor_from_numpy, ones_tensor_from_numpy)
from .nn import one_hot
from .tensor_ops import TensorBackend
from .tensor import Tensor

from typing import Any, Dict, Optional, Sequence, Tuple


class Embedding(Module):
    def __init__(self, num_embeddings: int, embedding_dim: int, backend: TensorBackend):
        super().__init__()
        """
        Maps one-hot word vectors from a dictionary of fixed size to embeddings.

        Args:
            num_embeddings : The vocabulary size
            embedding_dim : The size of each embedding vector

        Attributes:
            weight : The learnable weights of shape (num_embeddings, embedding_dim) initialized from N(0, 1).
        """
        self.backend = backend
        self.num_embeddings = num_embeddings # Vocab size
        self.embedding_dim  = embedding_dim  # Embedding Dimension
        ### BEGIN YOUR SOLUTION
        init_weights = np.random.normal(size=(num_embeddings, embedding_dim))
        init_weights = tensor_from_numpy(init_weights, backend=backend)
        self.weights = Parameter(init_weights)
        ### END YOUR SOLUTION
    
    def forward(self, x: Tensor):
        """Maps word indices to one-hot vectors, and projects to embedding vectors.

        Args:
            x : Tensor of shape (batch_size, seq_len)

        Returns:
            output : Tensor of shape (batch_size, seq_len, embedding_dim)
        """
        bs, seq_len = x.shape
        ### BEGIN YOUR SOLUTION
        oh = one_hot(x, self.num_embeddings)
        agg = oh.view(bs * seq_len, self.num_embeddings)
        return (agg @ self.weights.value).view(bs, seq_len, self.embedding_dim)
        ### END YOUR SOLUTION

    
class Dropout(Module):
    def __init__(self, p_dropout: float=0.1):
        super().__init__()
        """During training, randomly zeroes some of the elements of the input tensor with probability :attr:`p_dropout`.

        Attributes: 
            p_dropout : Probability an element will be zeroed.
        """
        self.p_dropout = p_dropout

    def forward(self, x: Tensor) -> Tensor: 
        """During training, randomly zero out elements of a tensor and scale by (1 - p_dropout)
        
        Args: 
            x : Tensor of shape (*)
        
        Returns: 
            output : Tensor of shape (*)
        """
        ### BEGIN YOUR SOLUTION
        if not self.training or self.p_dropout == 0:
            return x
        mask = np.random.binomial(1, 1 - self.p_dropout, size=x.shape)
        mask = tensor_from_numpy(mask, backend=x.backend)
        return mask * x / (1 - self.p_dropout)
        ### END YOUR SOLUTION


class Linear(Module):
    def __init__(self, in_size: int, out_size: int, bias: bool, backend: TensorBackend):
        super().__init__()
        """Applies a linear transformation to the incoming data. (Same as PyTorch)

        Parameters:
            in_size  - The size of the dimension the transformation will be applied to
            out_size - The size of the resulting transformation's dimension
            bias     - If True, then add an additive bias

        Attributes:
            weights - The learnable weights of shape (in_size, out_size) initialized from Uniform(-1/sqrt(in_size), 1/sqrt(in_size)).
            bias   - The learnable weights of shape (out_size, ) initialized from Uniform(-1/sqrt(in_size), 1/sqrt(in_size)).
        """
        self.out_size = out_size
        self.has_bias = bias
        ### BEGIN YOUR SOLUTION
        self.weights = self.RParam(backend, in_size, out_size)
        if bias:
            self.bias = self.RParam(backend, out_size,)
        ### END YOUR SOLUTION

    @classmethod
    def RParam(cls, backend, *shape):
        r = 0.1 * (rand(shape, backend=backend) - 0.5)
        return Parameter(r)

    def forward(self, x: Tensor):
        """Applies a linear transformation to the incoming data.
        
        Args: 
            x : Tensor of shape (n, in_size)
        
        Returns:
            output : Tensor of shape (n, out_size)
        """
        batch, in_size = x.shape
        ### BEGIN YOUR SOLUTION
        if self.has_bias:
            return x.view(batch, in_size) @ self.weights.value.view(in_size, self.out_size) + self.bias.value
        return x.view(batch, in_size) @ self.weights.value.view(in_size, self.out_size)
        ### END YOUR SOLUTION


class LayerNorm1d(Module):
    def __init__(self, dim: int, eps: float, backend: TensorBackend, fused_kernels: bool=True):
        super().__init__()
        """Applies Layer Normalization over a mini-batch of 1-dimensional inputs.
        
        Args: 
            dim : Expected size of the last dimension to apply layer normalization.
            eps : A value added for numerical stability.
        
        Attributes: 
            weights : the learnable weights of the module of shape (self.dim, ) initialized to 1.
            bias    : the learnable bias of the module of shape (self.dim, ) initialized to 0.
        """
        self.dim = dim
        self.eps = eps
        ### BEGIN YOUR SOLUTION
        self.weights = Parameter(ones((self.dim,), backend))
        self.bias = Parameter(zeros((self.dim,), backend))
        self.fused_kernels = fused_kernels
        ### END YOUR SOLUTION

    def forward(self, x: Tensor) -> Tensor:
        """Applies Layer Normalization over a mini-batch of inputs. 
        NOTE: You can assume the input to this layer is a 2D tensor of shape (batch_size, dim)
        You will use implicit broadcasting in miniTorch to use the weight and bias.
        
        Input: 
            x - Tensor of shape (bs, dim)
        
        Output: 
            output - Tensor of shape (bs, dim)
        """
        if  self.fused_kernels:
            return x.layernorm(self.weights.value, self.bias.value)

        batch, dim = x.shape
        ### BEGIN YOUR SOLUTION
        mean = x.mean(dim=1)
        std = (x.var(dim=1) + self.eps) ** 0.5
        return self.weights.value * (x - mean) / std + self.bias.value
        ### END YOUR SOLUTION
