from hdxms_datasets import DataVault


class TestDataVault:
    def test_empty_vault(self, tmp_path):
        vault = DataVault(cache_dir=tmp_path)
        assert len(vault.datasets) == 0

        idx = vault.index
        assert len(idx) > 0
