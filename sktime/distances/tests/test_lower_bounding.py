# -*- coding: utf-8 -*-
"""Test suite for lower bounding techniques."""
import numpy as np
import pandas as pd
import pytest

from sktime.distances.lower_bounding import LowerBounding, numba_create_bounding_matrix
from sktime.distances.tests._utils import create_test_distance_numpy


def _validate_bounding_result(
    matrix: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    all_finite: bool = False,
    all_infinite: bool = False,
    is_gradient_bounding: bool = False,
):
    """Validate the bounding matrix is what is expected.

    Parameters
    ----------
    matrix: np.ndarray (2d array)
        Bounding matrix.
    x: np.ndarray (1d, 2d or 3d array)
        First timeseries.
    y: np.ndarray (1d, 2d or 3d array)
        Second timeseries.
    all_finite: bool, default = False
        Boolean that when true will check all the values are finite.
    all_infinite: bool, default = False
        Boolean that when true will check all the values (aside the middle diagonal)
        are infinite.
    is_gradient_bounding: bool, default = False
        Boolean that when true marks the bounding matrix as generated by an algorithm
        that uses a gradient and therefore the first a second column are allowed to
        be finite (aside the first and last element in the matrix).
    """
    assert isinstance(matrix, np.ndarray), (
        f"A bounding matrix must be of type np.ndarray. Instead one was provided with "
        f"{type(matrix)} type."
    )
    assert matrix.ndim == 2, (
        f"A bounding matrix must have two dimensions. Instead one was provided with "
        f"{matrix.ndim} dimensions."
    )
    assert matrix.shape == (len(x), len(y)), (
        f"A bounding matrix with shape len(x) by len(y) is expected ({len(x), len(y)}. "
        f"Instead one was given with shape {matrix.shape}"
    )

    unique, counts = np.unique(matrix, return_counts=True)
    count_dict = dict(zip(unique, counts))

    for key in count_dict:
        if np.isfinite(key):
            assert count_dict[key] >= len(y) or all_infinite is False, (
                "All the values in the bounding matrix should be finite. A infinite "
                "value was found (aside from the diagonal)."
            )
        else:
            if is_gradient_bounding:
                max_infinite = len(y) + len(x) - 2  # -2 as 0,0 and n,m should be finite
                assert count_dict[key] >= max_infinite or all_finite is False, (
                    "All values in the bounding matrix should be infinite. Aside"
                    "from the first column and last column."
                )
            else:
                assert all_finite is False, (
                    "All values in the bounding matrix should be"
                    "infinite. A finite value was found"
                )


def _validate_bounding(
    x: np.ndarray,
    y: np.ndarray,
) -> None:
    """Test each lower bounding with different parameters.

    The amount of finite vs infinite values are estimated and are checked that many
    is around the amount in the matrix.

    Parameters
    ----------
    x: np.ndarray (1d, 2d or 3d)
        First timeseries
    y: np.ndarray (1d, 2d, or 3d)
        Second timeseries
    """
    no_bounding = LowerBounding.NO_BOUNDING
    no_bounding_result = no_bounding.create_bounding_matrix(x, y)
    _validate_bounding_result(no_bounding_result, x, y, all_finite=True)

    sakoe_chiba = LowerBounding.SAKOE_CHIBA
    _validate_bounding_result(
        sakoe_chiba.create_bounding_matrix(x, y, sakoe_chiba_window_radius=0.25),
        x,
        y,
    )
    _validate_bounding_result(
        sakoe_chiba.create_bounding_matrix(x, y, sakoe_chiba_window_radius=0.25),
        x,
        y,
    )
    _validate_bounding_result(
        sakoe_chiba.create_bounding_matrix(x, y, sakoe_chiba_window_radius=1.0),
        x,
        y,
        all_finite=True,
    )
    _validate_bounding_result(
        sakoe_chiba.create_bounding_matrix(x, y, sakoe_chiba_window_radius=0.0),
        x,
        y,
        all_infinite=True,
    )

    itakura_parallelogram = LowerBounding.ITAKURA_PARALLELOGRAM

    _validate_bounding_result(
        itakura_parallelogram.create_bounding_matrix(x, y, itakura_max_slope=0.2),
        x,
        y,
        is_gradient_bounding=True,
    )
    _validate_bounding_result(
        itakura_parallelogram.create_bounding_matrix(x, y, itakura_max_slope=0.3),
        x,
        y,
        is_gradient_bounding=True,
    )
    _validate_bounding_result(
        itakura_parallelogram.create_bounding_matrix(x, y, itakura_max_slope=1.0),
        x,
        y,
        all_finite=True,
        is_gradient_bounding=True,
    )
    _validate_bounding_result(
        itakura_parallelogram.create_bounding_matrix(x, y, itakura_max_slope=0.0),
        x,
        y,
        all_infinite=True,
        is_gradient_bounding=True,
    )


def _validate_numba_bounding(
    x: np.ndarray,
    y: np.ndarray,
) -> None:
    """Test each lower bounding with different parameters.

    The amount of finite vs infinite values are estimated and are checked that many
    is around the amount in the matrix.

    Parameters
    ----------
    x: np.ndarray (1d, 2d or 3d)
        First timeseries
    y: np.ndarray (1d, 2d, or 3d)
        Second timeseries
    """
    x_y_max = max(len(x), len(y))
    no_bounding_result = numba_create_bounding_matrix(x, y)
    _validate_bounding_result(no_bounding_result, x, y, all_finite=True)

    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, sakoe_chiba_window_radius=2),
        x,
        y,
    )
    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, sakoe_chiba_window_radius=3),
        x,
        y,
    )
    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, sakoe_chiba_window_radius=x_y_max),
        x,
        y,
        all_finite=True,
    )
    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, sakoe_chiba_window_radius=0),
        x,
        y,
        all_infinite=True,
    )

    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, itakura_max_slope=0.2),
        x,
        y,
        is_gradient_bounding=True,
    )
    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, itakura_max_slope=0.3),
        x,
        y,
        is_gradient_bounding=True,
    )
    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, itakura_max_slope=1.0),
        x,
        y,
        all_finite=True,
        is_gradient_bounding=True,
    )
    _validate_bounding_result(
        numba_create_bounding_matrix(x, y, itakura_max_slope=0.0),
        x,
        y,
        all_infinite=True,
        is_gradient_bounding=True,
    )


def test_lower_bounding() -> None:
    """Test for various lower bounding methods."""
    no_bounding = LowerBounding.NO_BOUNDING
    no_bounding_int = LowerBounding(1)
    assert (
        no_bounding_int is no_bounding
    ), "No bounding must be able to be constructed using the enum and a int value."

    sakoe_chiba = LowerBounding.SAKOE_CHIBA
    sakoe_chiba_int = LowerBounding(2)
    assert (
        sakoe_chiba_int is sakoe_chiba
    ), "Sakoe chiba must be able to be constructed using the enum and a int value."

    itakura_parallelogram = LowerBounding.ITAKURA_PARALLELOGRAM
    itakura_parallelogram_int = LowerBounding(3)
    assert itakura_parallelogram_int is itakura_parallelogram, (
        "Itakura parallelogram must be able to be constructed using the enum and a int "
        "value"
    )

    _validate_bounding(
        x=np.array([10.0]),
        y=np.array([15.0]),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10),
        y=create_test_distance_numpy(10, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 1),
        y=create_test_distance_numpy(10, 1, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 10),
        y=create_test_distance_numpy(10, 10, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 10, 1),
        y=create_test_distance_numpy(10, 10, 1, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 10, 10),
        y=create_test_distance_numpy(10, 10, 10, random_state=2),
    )


def test_incorrect_parameters() -> None:
    """Test to check correct errors raised."""
    numpy_x = create_test_distance_numpy(10, 10)
    numpy_y = create_test_distance_numpy(10, 10, random_state=2)

    df_x = pd.DataFrame(numpy_x)

    series_x = df_x.iloc[0]

    numpy_4d = np.array([[[[1, 2, 3]]]])

    no_bounding = LowerBounding.NO_BOUNDING
    sakoe_chiba = LowerBounding.SAKOE_CHIBA

    with pytest.raises(ValueError):  # Try pass data frame in y
        no_bounding.create_bounding_matrix(numpy_x, df_x)

    with pytest.raises(ValueError):  # Try pass data frame in x
        no_bounding.create_bounding_matrix(df_x, numpy_y)

    with pytest.raises(ValueError):  # Try pass series in y
        no_bounding.create_bounding_matrix(numpy_x, series_x)

    with pytest.raises(ValueError):  # Try pass series in x
        no_bounding.create_bounding_matrix(series_x, numpy_y)

    with pytest.raises(ValueError):  # Try pass 4d numpy in y
        no_bounding.create_bounding_matrix(numpy_x, numpy_4d)

    with pytest.raises(ValueError):  # Try pass 4d numpy in x
        no_bounding.create_bounding_matrix(numpy_4d, numpy_y)

    with pytest.raises(ValueError):  # Try pass float to sakoe
        sakoe_chiba.create_bounding_matrix(
            numpy_x, numpy_y, sakoe_chiba_window_radius=1.2
        )

    with pytest.raises(ValueError):  # Try pass both window and gradient
        sakoe_chiba.create_bounding_matrix(
            numpy_x, numpy_y, sakoe_chiba_window_radius=1.2, itakura_max_slope=10.0
        )


def test_numba_lower_bounding() -> None:
    """Test numba implementation of bounding."""
    _validate_bounding(
        x=np.array([10.0]),
        y=np.array([15.0]),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10),
        y=create_test_distance_numpy(10, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 1),
        y=create_test_distance_numpy(10, 1, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 10),
        y=create_test_distance_numpy(10, 10, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 10, 1),
        y=create_test_distance_numpy(10, 10, 1, random_state=2),
    )

    _validate_bounding(
        x=create_test_distance_numpy(10, 10, 10),
        y=create_test_distance_numpy(10, 10, 10, random_state=2),
    )
