# -*- coding: utf-8 -*-
#
from .newton import newton, NewtonConvergenceError


def natural(
    problem,
    u0,
    lambda0,
    callback,
    lambda_stepsize0=1.0e-1,
    lambda_stepsize_max=1.0e0,
    lambda_stepsize_aggressiveness=2,
    max_newton_steps=5,
    newton_tol=1.0e-12,
    max_steps=float("inf"),
    verbose=True,
    first_order_predictor=True,
):
    """Natural parameter continuation
    """
    lmbda = lambda0

    k = 0
    try:
        u, _ = newton(
            lambda u: problem.f(u, lmbda),
            lambda u, rhs: problem.jacobian_solver(u, lmbda, rhs),
            problem.norm2_r,
            u0,
            tol=newton_tol,
            max_iter=max_newton_steps,
        )
    except NewtonConvergenceError as e:
        print("No convergence for initial step.".format(lmbda))
        raise e

    callback(k, lmbda, u)
    k += 1

    lambda_stepsize = lambda_stepsize0

    while True:
        if k > max_steps:
            break

        if verbose:
            print(
                "Step {}: lambda  {:.3e} + {:.3e}  ->  {:.3e}".format(
                    k, lmbda, lambda_stepsize, lmbda + lambda_stepsize
                )
            )

        # Predictor
        lmbda += lambda_stepsize
        if first_order_predictor:
            du_dlmbda = problem.jacobian_solver(u, lmbda, -problem.df_dlmbda(u, lmbda))
            u0 = u + du_dlmbda * lambda_stepsize
        else:
            u0 = u

        # Corrector
        try:
            u, newton_steps = newton(
                lambda u: problem.f(u, lmbda),
                lambda u, rhs: problem.jacobian_solver(u, lmbda, rhs),
                problem.norm2_r,
                u0,
                tol=newton_tol,
                max_iter=max_newton_steps,
            )
        except NewtonConvergenceError:
            if verbose:
                print("No convergence for lambda={}.".format(lmbda))
            lmbda -= lambda_stepsize
            lambda_stepsize /= 2
            continue

        lambda_stepsize *= (
            1
            + lambda_stepsize_aggressiveness
            * ((max_newton_steps - newton_steps) / (max_newton_steps - 1)) ** 2
        )
        lambda_stepsize = min(lambda_stepsize, lambda_stepsize_max)

        callback(k, lmbda, u)
        k += 1

    return