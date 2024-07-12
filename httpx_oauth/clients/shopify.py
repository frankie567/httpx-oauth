from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, cast

from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2

AUTHORIZE_ENDPOINT = "https://{shop}.myshopify.com/admin/oauth/authorize"
ACCESS_TOKEN_ENDPOINT = "https://{shop}.myshopify.com/admin/oauth/access_token"
BASE_SCOPES = ["read_orders"]
PROFILE_ENDPOINT = "https://{shop}.myshopify.com/admin/api/{api_version}/shop.json"


LOGO_SVG = """
<svg width="256px" height="292px" viewBox="0 0 256 292" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="xMidYMid">
	<g>
		<path d="M223.773626,57.3402078 C223.572932,55.8793405 222.29409,55.0718963 221.236945,54.9832175 C220.182133,54.8945386 197.853734,53.2399781 197.853734,53.2399781 C197.853734,53.2399781 182.346604,37.8448639 180.64537,36.1412966 C178.941803,34.4377293 175.616346,34.9558004 174.325836,35.336186 C174.134476,35.3921937 170.937371,36.3793293 165.646977,38.0152206 C160.466266,23.1101737 151.325344,9.41162582 135.241802,9.41162582 C134.798408,9.41162582 134.341011,9.43029505 133.883615,9.45596525 C129.309654,3.40713457 123.643542,0.779440373 118.74987,0.779440373 C81.285392,0.779440373 63.3862673,47.6135387 57.7738299,71.414474 C43.2164974,75.9254268 32.8737437,79.1318671 31.5528956,79.5472575 C23.4271131,82.0956074 23.1704111,82.3523094 22.1039313,90.0090275 C21.2988208,95.8058236 0.0369009009,260.235071 0.0369009009,260.235071 L165.714653,291.277334 L255.485648,271.856667 C255.485648,271.856667 223.971987,58.8010751 223.773626,57.3402078 L223.773626,57.3402078 Z M156.48972,40.8482763 C152.328815,42.1364532 147.598499,43.5996542 142.471461,45.1865388 C142.476129,44.1994032 142.480796,43.2262696 142.480796,42.1644571 C142.480796,32.8998514 141.194953,25.4414939 139.132003,19.5280151 C147.418807,20.5688247 152.937899,29.9967861 156.48972,40.8482763 L156.48972,40.8482763 Z M128.852258,21.3646006 C131.155574,27.1380602 132.65378,35.4225312 132.65378,46.6030666 C132.65378,47.1748118 132.649112,47.6975503 132.644445,48.2272897 C123.52686,51.0510108 113.620499,54.1174319 103.690802,57.1931876 C109.265901,35.6768995 119.716003,25.2851391 128.852258,21.3646006 L128.852258,21.3646006 Z M117.720729,10.8281537 C119.337951,10.8281537 120.966841,11.3765623 122.525722,12.4500431 C110.519073,18.099819 97.6489725,32.3304399 92.2138928,60.7473424 C84.2701352,63.2070135 76.506069,65.6106769 69.3277499,67.834649 C75.6939575,46.1596724 90.8113669,10.8281537 117.720729,10.8281537 L117.720729,10.8281537 Z" fill="#95BF46"></path>
		<path d="M221.236945,54.9832175 C220.182133,54.8945386 197.853734,53.2399781 197.853734,53.2399781 C197.853734,53.2399781 182.346604,37.8448639 180.64537,36.1412966 C180.008283,35.5065427 179.149498,35.1821649 178.251042,35.0421456 L165.723988,291.275001 L255.485648,271.856667 C255.485648,271.856667 223.971987,58.8010751 223.773626,57.3402078 C223.572932,55.8793405 222.29409,55.0718963 221.236945,54.9832175" fill="#5E8E3E"></path>
		<path d="M135.241802,104.585029 L124.173282,137.510551 C124.173282,137.510551 114.474617,132.334507 102.586984,132.334507 C85.1592573,132.334507 84.2818035,143.272342 84.2818035,146.028387 C84.2818035,161.066452 123.48252,166.828244 123.48252,202.052414 C123.48252,229.764553 105.90544,247.610004 82.2048516,247.610004 C53.7646126,247.610004 39.2212821,229.90924 39.2212821,229.90924 L46.8359944,204.750118 C46.8359944,204.750118 61.7853808,217.585214 74.4011133,217.585214 C82.6435785,217.585214 85.9970391,211.095323 85.9970391,206.353338 C85.9970391,186.736644 53.8369559,185.861524 53.8369559,153.629098 C53.8369559,126.500372 73.3089633,100.246767 112.614694,100.246767 C127.760108,100.246767 135.241802,104.585029 135.241802,104.585029" fill="#FFFFFF"></path>
	</g>
</svg>
"""


class ShopifyOAuth2AuthorizeParams(TypedDict, total=False):
    access_mode: Optional[Literal["per-user"]]


class ShopifyOAuth2(BaseOAuth2[ShopifyOAuth2AuthorizeParams]):
    """
    OAuth2 client for Shopify.

    The OAuth2 client for Shopify authenticates shop owners to allow making calls
    to the [Shopify Admin API](https://shopify.dev/docs/api/admin).
    """

    display_name = "Shopify"
    logo_svg = LOGO_SVG

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        shop: str,
        scopes: Optional[List[str]] = BASE_SCOPES,
        api_version: str = "2023-04",
        name: str = "shopify",
    ):
        """
        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            shop: The shop subdomain.
            scopes: The default scopes to be used in the authorization URL.
            api_version: The version of the Shopify Admin API.
            name: A unique name for the OAuth2 client.
        """
        authorize_endpoint = AUTHORIZE_ENDPOINT.format(shop=shop)
        access_token_endpoint = ACCESS_TOKEN_ENDPOINT.format(shop=shop)
        self.profile_endpoint = PROFILE_ENDPOINT.format(
            shop=shop, api_version=api_version
        )
        super().__init__(
            client_id,
            client_secret,
            authorize_endpoint,
            access_token_endpoint,
            name=name,
            base_scopes=scopes,
            token_endpoint_auth_method="client_secret_post",
        )

    async def get_id_email(self, token: str) -> Tuple[str, Optional[str]]:
        """
        Returns the id and the email (if available) of the authenticated user
        from the API provider.

        !!! warning "`get_id_email` is based on the `Shop` resource"
            The implementation of `get_id_email` calls the [Get Shop endpoint](https://shopify.dev/docs/api/admin-rest/2023-04/resources/shop#get-shop) of the Shopify Admin API.
            It means that it'll return you the **ID of the shop** and the **email of the shop owner**.

        Args:
            token: The access token.

        Returns:
            A tuple with the id and the email of the authenticated user.


        Raises:
            httpx_oauth.exceptions.GetIdEmailError:
                An error occurred while getting the id and email.

        Examples:
            ```py
            user_id, user_email = await client.get_id_email("TOKEN")
            ```
        """
        async with self.get_httpx_client() as client:
            response = await client.get(
                self.profile_endpoint,
                headers={"X-Shopify-Access-Token": token},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response=response)

            data = cast(Dict[str, Any], response.json())
            shop = data["shop"]
            return str(shop["id"]), shop["email"]
