from attp_client.misc.fixed_basemodel import FixedBaseModel


class ICatalogResponse(FixedBaseModel):
    catalog_id: int
    organization_id: int