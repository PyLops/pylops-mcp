from pylops_mcp import server


def test_get_operator_schema() -> None:
    res = server.get_operator("Convolve1D")
    assert res["name"] == "Convolve1D"
    assert res["kind"] == "operator"
    assert res["module"].startswith("pylops.signalprocessing")
    assert res["pylops_version"]
    assert any(p["name"] == "dims" for p in res["parameters"])


def test_get_solver() -> None:
    res = server.get_solver("cgls")
    assert res["kind"] == "solver"
    assert "signature" in res


def test_search_finds_convolution() -> None:
    res = server.search("convolve1d")
    assert "Convolve1D" in [h["name"] for h in res["results"]]
    assert res["pylops_version"]


def test_search_solver_kind() -> None:
    res = server.search("cg", kind="solver")
    assert {h["kind"] for h in res["results"]} == {"solver"}


def test_unknown_name_gives_suggestions() -> None:
    res = server.get_operator("Convolve1")
    assert "error" in res
    assert "Convolve1D" in res["suggestions"]
    assert res["pylops_version"]


def test_list_operators_module_filter() -> None:
    res = server.list_operators("basicoperators")
    assert "Identity" in res["operators"]
    assert "Convolve1D" not in res["operators"]


def test_list_solvers_module_filter() -> None:
    res = server.list_solvers("sparsity")
    assert "fista" in res["solvers"]
    assert "cgls" not in res["solvers"]
    assert "cgls" in server.list_solvers()["solvers"]
