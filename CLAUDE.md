# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

GIS project analyzing Brussels traffic data. Pedagogical project to learn open-source geospatial tools (PostGIS, GeoServer, FastAPI, Leaflet, GDAL, Shapely) as alternatives to Esri/ArcGIS.

## Stack (expected)

- **Data processing**: Python (Jupyter notebooks, GDAL, Shapely, GeoPandas)
- **Backend**: FastAPI serving GeoJSON or vector tiles
- **Database**: PostGIS
- **Frontend**: Leaflet (open-source equivalent of ArcGIS Maps SDK)
- **Data format**: GeoJSON, GeoPackage, or Shapefile

## Development

```bash
docker compose up        # démarrer tous les services (db + api)
docker compose down -v   # arrêter et supprimer les volumes
docker compose logs -f api  # suivre les logs du scheduler
```

## Variables d'environnement

Créer un fichier `.env` à la racine (non versionné) :

```
DATABASE_URL=postgresql://postgres:postgres@db:5432/traffic
RETENTION_DAYS=30
```
