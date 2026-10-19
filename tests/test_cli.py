
import json
import sys

from changescope.cli import main


def test_cli_parser_accepts_json_flag(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "changescope",
            "report",
            "--repo",
            ".",
            "--base",
            "HEAD~1",
            "--json",
        ],
    )

    try:
        main()
    except Exception as exc:
        if isinstance(exc, SystemExit):
            raise
    output = capsys.readouterr().out
    assert output


def test_cli_json_output_is_valid(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "changescope",
            "report",
            "--repo",
            ".",
            "--base",
            "HEAD~1",
            "--json",
        ],
    )

    main()
    output = capsys.readouterr().out
    data = json.loads(output)

    assert "changed_functions" in data
    assert "affected_functions" in data
    assert "recommended_tests" in data
