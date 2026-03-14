"""
Amazon Advertising API wrapper.
If credentials are configured in config/config.yaml, uses the real API.
Otherwise falls back to mock data with a clear notice.
"""
import os
import yaml
import pandas as pd

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def has_credentials() -> bool:
    try:
        cfg = load_config()
        creds = cfg.get("credentials", {})
        return all(
            creds.get(k, "") not in ("", None)
            for k in ["client_id", "client_secret", "refresh_token", "profile_id"]
        )
    except Exception:
        return False


def _setup_env():
    cfg = load_config()
    creds = cfg.get("credentials", {})
    os.environ["LWA_APP_ID"] = creds.get("client_id", "")
    os.environ["LWA_CLIENT_SECRET"] = creds.get("client_secret", "")
    os.environ["SP_API_REFRESH_TOKEN"] = creds.get("refresh_token", "")
    os.environ["ADVERTISING_API_PROFILE_ID"] = creds.get("profile_id", "")


def list_campaigns() -> tuple[pd.DataFrame, bool]:
    """Returns (dataframe, is_real_data)."""
    if not has_credentials():
        from ads.mock_ads_api import list_campaigns as mock_campaigns
        return mock_campaigns(), False

    try:
        _setup_env()
        from ad_api.api.sp import Campaigns

        c = Campaigns()
        resp = c.list_campaigns()
        data = resp.payload if hasattr(resp, "payload") else []
        df = pd.DataFrame(data)
        return df, True
    except Exception as e:
        from ads.mock_ads_api import list_campaigns as mock_campaigns
        return mock_campaigns(), False


def get_campaign_keywords(campaign_id: str = None) -> tuple[pd.DataFrame, bool]:
    """Returns (dataframe, is_real_data)."""
    if not has_credentials():
        from ads.mock_ads_api import get_campaign_keywords as mock_kws
        return mock_kws(campaign_id), False

    try:
        _setup_env()
        from ad_api.api.sp import Keywords

        kw_api = Keywords()
        resp = kw_api.list_keywords(
            campaignId=campaign_id if campaign_id else None
        )
        data = resp.payload if hasattr(resp, "payload") else []
        df = pd.DataFrame(data)
        return df, True
    except Exception:
        from ads.mock_ads_api import get_campaign_keywords as mock_kws
        return mock_kws(campaign_id), False


def get_search_terms() -> tuple[pd.DataFrame, bool]:
    """Returns (dataframe, is_real_data). Real API requires async report download."""
    if not has_credentials():
        from ads.mock_ads_api import get_search_terms as mock_st
        return mock_st(), False
    # Real search term report download is async; return mock with note
    from ads.mock_ads_api import get_search_terms as mock_st
    return mock_st(), False


def pause_keyword(keyword_id: str) -> bool:
    if not has_credentials():
        return False
    try:
        _setup_env()
        from ad_api.api.sp import Keywords
        kw_api = Keywords()
        kw_api.update_keywords(body=[{"keywordId": keyword_id, "state": "paused"}])
        return True
    except Exception:
        return False


def update_keyword_bid(keyword_id: str, new_bid: float) -> bool:
    if not has_credentials():
        return False
    try:
        _setup_env()
        from ad_api.api.sp import Keywords
        kw_api = Keywords()
        kw_api.update_keywords(body=[{"keywordId": keyword_id, "bid": new_bid}])
        return True
    except Exception:
        return False


def create_campaign(
    name: str,
    daily_budget: float = 5.0,
    targeting_type: str = "manual",
) -> tuple[str | None, bool]:
    """Returns (campaign_id or None, success)."""
    if not has_credentials():
        return None, False
    try:
        _setup_env()
        from ad_api.api.sp import Campaigns, AdGroups

        c = Campaigns()
        resp = c.create_campaigns(
            body=[
                {
                    "name": name,
                    "campaignType": "sponsoredProducts",
                    "targetingType": targeting_type,
                    "state": "enabled",
                    "dailyBudget": daily_budget,
                }
            ]
        )
        campaign_id = resp.payload[0]["campaignId"]

        ag = AdGroups()
        ag_resp = ag.create_ad_groups(
            body=[
                {
                    "campaignId": campaign_id,
                    "name": "default",
                    "defaultBid": 0.35,
                    "state": "enabled",
                }
            ]
        )
        ad_group_id = ag_resp.payload[0]["adGroupId"]
        return campaign_id, True
    except Exception:
        return None, False


def add_keywords_to_campaign(
    campaign_id: str,
    ad_group_id: str,
    keywords: list[str],
    bid: float = 0.35,
    match_type: str = "broad",
) -> bool:
    if not has_credentials():
        return False
    try:
        _setup_env()
        from ad_api.api.sp import Keywords

        kw_api = Keywords()
        body = [
            {
                "campaignId": campaign_id,
                "adGroupId": ad_group_id,
                "keywordText": kw,
                "matchType": match_type,
                "bid": bid,
                "state": "enabled",
            }
            for kw in keywords
        ]
        kw_api.create_keywords(body=body)
        return True
    except Exception:
        return False
