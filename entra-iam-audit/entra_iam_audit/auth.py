import msal


SCOPES = ["https://graph.microsoft.com/.default"]


class GraphAuth:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str | None = None):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None

    def get_token(self) -> str:
        if self._token:
            return self._token

        authority = f"https://login.microsoftonline.com/{self.tenant_id}"

        if self.client_secret:
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=authority,
                client_credential=self.client_secret,
            )
            result = app.acquire_token_for_client(scopes=SCOPES)
        else:
            app = msal.PublicClientApplication(self.client_id, authority=authority)
            flow = app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow:
                raise RuntimeError(f"Device flow failed: {flow}")
            print(flow["message"])
            result = app.acquire_token_by_device_flow(flow)

        if "access_token" not in result:
            raise RuntimeError(
                f"Authentication failed: {result.get('error_description', result.get('error', 'unknown'))}"
            )

        self._token = result["access_token"]
        return self._token
