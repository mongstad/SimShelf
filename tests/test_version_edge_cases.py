from simshelf.recording import Run


def snapshot(store, sim):
    with Run(sim["id"], workspace=store.path, capture_console=False) as run:
        pass
    return store.run(run.id)


def test_strings_and_docstrings_are_not_mistaken_for_comments(project):
    store, sim, root, source = project
    source.write_text('"""Original docstring"""\nSIMSHELF_VERSION="1.0"\nmessage="value # 1"\n')
    first = snapshot(store, sim)
    source.write_text(source.read_text().replace("value # 1", "value # 2"))
    second = snapshot(store, sim)
    assert second["source_change"] == "changed"
    source.write_text(source.read_text().replace("Original docstring", "Changed docstring"))
    third = snapshot(store, sim)
    assert third["structure_id"] != second["structure_id"]
    assert first["version"] == second["version"] == third["version"]


def test_source_is_deduplicated_for_repeated_identical_runs(project):
    store, sim, root, source = project
    first = snapshot(store, sim)
    second = snapshot(store, sim)
    assert second["source_change"] == "same"
    assert first["snapshot_id"] == second["snapshot_id"]
    assert len(list((store.path / "snapshots").glob("*.json"))) == 1
