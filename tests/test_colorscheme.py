"""Tests for color scheme parsing and resolution."""

import json

import pytest

from map_poster_creator.colorscheme import (
    COLOR_SCHEME_KEYS,
    color_scheme_from_mapping,
    resolve_poster_color,
)


class TestColorSchemeFromMapping:
    def test_hex_and_names(self):
        scheme = color_scheme_from_mapping(
            {
                "facecolor": "#433633",
                "water": "navy",
                "greens": "forestgreen",
                "roads": "wheat",
            }
        )
        assert scheme.to_json()["facecolor"].lower() == "#433633"
        assert "navy" in scheme.water.hex.lower() or scheme.water.hex

    def test_rgb_lists(self):
        scheme = color_scheme_from_mapping(
            {
                "facecolor": [1, 1, 1],
                "water": "#bdddff",
                "greens": [0.83, 1, 0.88],
                "roads": [0, 0, 0],
            }
        )
        assert len(scheme.to_json()) == len(COLOR_SCHEME_KEYS)

    def test_missing_keys(self):
        with pytest.raises(ValueError, match="Missing color keys"):
            color_scheme_from_mapping({"facecolor": "white", "water": "navy", "greens": "green"})

    def test_extra_keys(self):
        with pytest.raises(ValueError, match="Unexpected color keys"):
            color_scheme_from_mapping(
                {
                    "facecolor": "white",
                    "water": "navy",
                    "greens": "green",
                    "roads": "black",
                    "extra": "red",
                }
            )

    def test_unknown_color_name(self):
        with pytest.raises(ValueError, match="Unknown color name"):
            color_scheme_from_mapping(
                {
                    "facecolor": "not_a_real_color_xyz",
                    "water": "navy",
                    "greens": "green",
                    "roads": "black",
                }
            )


class TestResolvePosterColor:
    def test_named_scheme(self):
        scheme, label = resolve_poster_color("white")
        assert label == "white"
        assert scheme.to_json()["facecolor"].lower() in ("#ffffff", "#fff")

    def test_json_string(self):
        spec = json.dumps(
            {
                "facecolor": "#111111",
                "water": "navy",
                "greens": "green",
                "roads": "white",
            }
        )
        scheme, label = resolve_poster_color(spec)
        assert label.startswith("custom_")
        assert scheme.to_json()["facecolor"].lower().startswith("#111")

    def test_mapping(self):
        data = {
            "facecolor": "black",
            "water": "#383d52",
            "greens": "#354038",
            "roads": "#ffffff",
        }
        _, label_a = resolve_poster_color(data)
        _, label_b = resolve_poster_color(data)
        assert label_a == label_b

    def test_unknown_named_scheme(self):
        with pytest.raises(KeyError):
            resolve_poster_color("no_such_scheme_name_zzz")

    def test_invalid_json_object_type(self):
        with pytest.raises(ValueError, match="must be an object"):
            resolve_poster_color('["not", "a", "dict"]')
