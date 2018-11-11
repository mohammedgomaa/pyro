from __future__ import absolute_import, division, print_function

import torch
from torch.distributions import Normal

import pytest
from pyro.contrib.bnn import HiddenLayer
from tests.common import assert_equal


@pytest.mark.parametrize("non_linearity", ['linear', 'relu'])
@pytest.mark.parametrize("covariance", ['diagonal', 'cholesky'])
@pytest.mark.parametrize("include_hidden_bias", [False, True])
def test_hidden_layer_rsample(non_linearity, include_hidden_bias, covariance, B=2, D=3, H=4, N=900000):
    X = torch.randn(B, D)
    A_mean = torch.rand(D, H)
    if covariance=='diagonal':
        A_scale = 0.3 * torch.exp(0.3 * torch.rand(D, H))
    elif covariance=='cholesky':
        A_scale = 0.3 * torch.exp(0.3 * torch.rand(D, D, H))

    # test naive weight space sampling against sampling in pre-activation space
    dist1 = HiddenLayer(X=X, A_mean=A_mean, A_scale=A_scale, non_linearity=non_linearity,
                        include_hidden_bias=include_hidden_bias, weight_space_sampling=True)
    dist2 = HiddenLayer(X=X, A_mean=A_mean, A_scale=A_scale, non_linearity=non_linearity,
                        include_hidden_bias=include_hidden_bias, weight_space_sampling=False)

    out1 = dist1.rsample(sample_shape=(N,))
    out1_mean, out1_var = out1.mean(0), out1.var(0)
    out2 = dist2.rsample(sample_shape=(N,))
    out2_mean, out2_var = out2.mean(0), out2.var(0)

    assert_equal(out1_mean, out2_mean, prec=0.003)
    assert_equal(out1_var, out2_var, prec=0.003)
    return


@pytest.mark.parametrize("non_linearity", ['linear', 'relu'])
@pytest.mark.parametrize("include_hidden_bias", [True, False])
def test_hidden_layer_log_prob(non_linearity, include_hidden_bias, B=2, D=3, H=2, N=1000000,
                               leaky_epsilon=0.1, hard_sigmoid_alpha=1.0):
    X = torch.randn(B, D)
    A_mean = torch.rand(D, H)
    A_scale = 0.3 * torch.exp(0.3 * torch.rand(D, H))
    dist = HiddenLayer(X=X, A_mean=A_mean, A_scale=A_scale,
                       non_linearity=non_linearity, include_hidden_bias=include_hidden_bias)

    A_dist = Normal(A_mean, A_scale)
    A_prior = Normal(torch.zeros(D, H), torch.ones(D, H))
    kl = torch.distributions.kl.kl_divergence(A_dist, A_prior).sum()
    assert_equal(kl, dist.KL, prec=0.01)
