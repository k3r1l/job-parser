from src.filters import is_relevant_location, is_relevant_title, is_uk_relevant


class TestIsRelevantTitle:
    def test_data_scientist(self):
        assert is_relevant_title("Senior Data Scientist")

    def test_machine_learning(self):
        assert is_relevant_title("Machine Learning Engineer")

    def test_lead_data(self):
        assert is_relevant_title("Lead Data Analyst")

    def test_case_insensitive(self):
        assert is_relevant_title("SENIOR DATA SCIENTIST")

    def test_irrelevant_role(self):
        assert not is_relevant_title("Software Engineer")

    def test_irrelevant_short(self):
        assert not is_relevant_title("PM")

    def test_ml_engineer(self):
        assert is_relevant_title("ML Engineer")


class TestIsRelevantLocation:
    def test_london(self):
        assert is_relevant_location("London, UK")

    def test_remote(self):
        assert is_relevant_location("Remote (United Kingdom)")

    def test_hybrid(self):
        assert is_relevant_location("Hybrid - London")

    def test_no_match(self):
        assert not is_relevant_location("New York, USA")


class TestIsUkRelevant:
    def test_london_passes(self):
        assert is_uk_relevant("Senior Data Scientist London, UK")

    def test_uk_remote_passes(self):
        assert is_uk_relevant("Lead ML Engineer Cardiff, London or Remote (UK)")

    def test_no_location_passes(self):
        assert is_uk_relevant("Senior Data Scientist")

    def test_san_francisco_rejected(self):
        assert not is_uk_relevant("ML Engineer San Francisco, CA")

    def test_riga_rejected(self):
        assert not is_uk_relevant("Senior Data Scientist Riga, Latvia")

    def test_lisbon_rejected(self):
        assert not is_uk_relevant("Senior Data Scientist Lisbon, Portugal")

    def test_sunnyvale_rejected(self):
        assert not is_uk_relevant("Staff Data Scientist Sunnyvale, California USA")

    def test_barcelona_rejected(self):
        assert not is_uk_relevant("Lead Data Scientist Barcelona")

    def test_united_states_rejected(self):
        assert not is_uk_relevant("Senior DS United States, Los Angeles, CA")
