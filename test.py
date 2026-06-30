from services.geoapify_service import GeoapifyService

geo = GeoapifyService()

result = geo.search_places(
    latitude=10.3528744,
    longitude=76.5120396,
    category="tourism"
)

print(result)