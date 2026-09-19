const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search';
const ELEVATION_URL = 'https://api.open-meteo.com/v1/elevation';

export default async function handler(req: any, res: any) {
  res.setHeader('Cache-Control', 's-maxage=3600, stale-while-revalidate=86400');
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const query = String(req.query?.q || '').trim().slice(0, 120);
  if (query.length < 2) return res.status(400).json({ error: 'Enter at least two characters.' });

  try {
    const params = new URLSearchParams({ q: query, format: 'jsonv2', limit: '5', addressdetails: '1', 'accept-language': 'en' });
    const geoResponse = await fetch(`${NOMINATIM_URL}?${params}`, {
      headers: { 'User-Agent': 'Safe2Peak/1.0 (altitude safety application)', Accept: 'application/json' },
    });
    if (!geoResponse.ok) throw new Error(`Location provider returned ${geoResponse.status}`);

    const places = (await geoResponse.json()) as Array<{ place_id: number; display_name: string; lat: string; lon: string; type?: string }>;
    if (!places.length) return res.status(404).json({ error: 'No matching location found.' });

    const latitudes = places.map(place => place.lat).join(',');
    const longitudes = places.map(place => place.lon).join(',');
    const elevationResponse = await fetch(`${ELEVATION_URL}?latitude=${latitudes}&longitude=${longitudes}`);
    if (!elevationResponse.ok) throw new Error(`Elevation provider returned ${elevationResponse.status}`);
    const elevationPayload = (await elevationResponse.json()) as { elevation?: number[] };

    const results = places.map((place, index) => ({
      id: String(place.place_id),
      name: place.display_name,
      latitude: Number(place.lat),
      longitude: Number(place.lon),
      elevation: Math.max(0, Math.round(elevationPayload.elevation?.[index] ?? 0)),
      type: place.type || 'place',
    }));
    return res.status(200).json({ results, attribution: 'Location © OpenStreetMap contributors; elevation © Open-Meteo' });
  } catch (error) {
    console.error('Location lookup failed', error);
    return res.status(502).json({ error: 'Location service is temporarily unavailable.' });
  }
}
