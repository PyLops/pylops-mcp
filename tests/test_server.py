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


def test_get_factory_operator() -> None:
    res = server.get_operator("FFT")
    assert res["kind"] == "operator"
    assert "signature" in res


def test_get_workflow() -> None:
    res = server.get_workflow("MDD")
    assert res["kind"] == "workflow"
    assert "MDD" in server.list_workflows()["workflows"]
    assert "MDD" not in server.list_operators()["operators"]


def test_search_workflow_kind() -> None:
    res = server.search("inversion", kind="workflow")
    assert res["results"]
    assert {h["kind"] for h in res["results"]} == {"workflow"}


def test_unknown_workflow_gives_suggestions() -> None:
    res = server.get_workflow("PrestackInversio")
    assert "PrestackInversion" in res["suggestions"]


def test_default_is_latest_version() -> None:
    versions = server.list_versions()
    latest = versions["pylops"]["default"]
    assert server.get_operator("Convolve1D")["pylops_version"] == latest
    assert latest == versions["pylops"]["versions"][-1]
    prox_latest = versions["pyproximal"]["default"]
    assert server.get_proxoperator("L1")["pyproximal_version"] == prox_latest
    assert prox_latest == versions["pyproximal"]["versions"][-1]


def test_explicit_older_version() -> None:
    res = server.get_operator("Convolve1D", pylops_version="2.4")
    assert res["pylops_version"] == "2.4.0"
    assert server.search("convolve1d", pylops_version="2.4.0")["pylops_version"] == (
        "2.4.0"
    )
    assert server.list_solvers(pylops_version="2.4")["pylops_version"] == "2.4.0"


def test_unknown_version() -> None:
    res = server.get_operator("Convolve1D", pylops_version="9.9")
    assert "error" in res
    assert "2.4.0" in res["available_versions"]
    assert "error" in server.list_operators(pylops_version="1.0")


def test_get_proxoperator() -> None:
    res = server.get_proxoperator("L1")
    assert res["name"] == "L1"
    assert res["kind"] == "operator"
    assert res["module"].startswith("pyproximal.proximal")
    assert res["pyproximal_version"]
    assert "pylops_version" not in res
    assert any(p["name"] == "sigma" for p in res["parameters"])


def test_get_proxsolver() -> None:
    res = server.get_proxsolver("ProximalGradient")
    assert res["kind"] == "solver"
    assert res["module"].startswith("pyproximal.optimization")
    assert "signature" in res


def test_prox_factory_and_case_insensitive() -> None:
    assert server.get_proxoperator("Simplex")["kind"] == "operator"
    assert server.get_proxsolver("admm")["name"] == "ADMM"


def test_prox_lists_and_module_filter() -> None:
    ops = server.list_proxperators()
    assert {"Box", "L1", "Simplex"} <= set(ops["operators"])
    assert ops["pyproximal_version"]
    assert "ADMM" not in ops["operators"]
    sol = server.list_proxsolvers("primaldual")
    assert "PrimalDual" in sol["solvers"]
    assert "ADMM" not in sol["solvers"]
    assert "ADMM" in server.list_proxsolvers()["solvers"]


def test_prox_unknown_name_gives_suggestions() -> None:
    res = server.get_proxsolver("ProximalGradien")
    assert "ProximalGradient" in res["suggestions"]
    assert "Box" in server.get_proxoperator("Bx")["suggestions"]


def test_prox_explicit_and_unknown_version() -> None:
    res = server.get_proxoperator("L1", pyproximal_version="0.10")
    assert res["pyproximal_version"] == "0.10.0"
    assert server.list_proxsolvers(pyproximal_version="0.9")["pyproximal_version"] == (
        "0.9.0"
    )
    bad = server.get_proxsolver("ADMM", pyproximal_version="9.9")
    assert "error" in bad
    assert "0.9.0" in bad["available_versions"]


def test_search_prox_kinds() -> None:
    res = server.search("admm", kind="proxsolver")
    assert "ADMM" in [h["name"] for h in res["results"]]
    assert {h["kind"] for h in res["results"]} == {"proxsolver"}
    assert "pylops_version" not in res
    assert res["pyproximal_version"]
    assert {h["kind"] for h in server.search("l1", kind="proxoperator")["results"]} == {
        "proxoperator"
    }


def test_search_all_spans_both_packages() -> None:
    res = server.search("convolve")
    assert res["pylops_version"] and res["pyproximal_version"]
    assert {"operator", "proxoperator"} <= {h["kind"] for h in res["results"]}
