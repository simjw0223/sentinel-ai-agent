# Sentinel AI Agent

Interactive satellite data download chatbot powered by LangChain and Streamlit. Chat in natural language to automatically search and download Sentinel-1 (SAR) and Sentinel-2 (Optical) imagery with intelligent location recognition.

<p align="center">
  <img src="https://github.com/user-attachments/assets/a38c1dda-f12c-4d97-bc84-6d330766b2fb" width="750" />
</p>


---

## Features

- **Natural Language Interface** - Chat-based UI using Streamlit
- **Intelligent Location Recognition** - Automatically converts place names to coordinates using geopy
- **Multi-Satellite Support** - Downloads both Sentinel-1 (SAR) and Sentinel-2 (Optical) imagery
- **LangChain Agent** - GPT-4o-mini powered agent with intelligent tool selection
- **Automated Workflow** - Extracts location and date from natural language, then searches and downloads
- **Dual Interface Modes** - Chat Agent and Direct Download options
- **Real-time STAC Search** - Searches satellite scenes via AWS Element84 STAC API
- **Cloud Filtering** - Sentinel-2 downloads only scenes with <20% cloud cover

---

## Tech Stack

- **Python** - Core language
- **Streamlit** - Interactive chat UI
- **OpenAI API** - GPT-4o-mini for natural language understanding
- **LangChain** - Agent framework and tool orchestration
- **geopy** - Geocoding for location name → coordinates conversion
- **pystac-client** - STAC API client for satellite data search
- **requests** - HTTP client for data download
- **python-dotenv** - Environment variable management

---

## How It Works

### Workflow

1. **User Input**: User sends a natural language request (e.g., "부산 광안대교 근처 2023년 6월 Sentinel-2 영상 내려줘")
2. **Location Geocoding**: Agent uses geopy to convert "부산 광안대교" → lat: 35.1456, lon: 129.1283
3. **Parameter Extraction**: GPT-4o-mini extracts satellite type, date, and coordinates
4. **STAC Search**: Tool searches for matching scenes within ±10 days
5. **Scene Selection**: Selects the scene closest to requested date with optimal conditions
6. **Download**: Downloads imagery bands (VV/VH for SAR, RGB for Optical) as GeoTIFF files
7. **Response**: Agent synthesizes results into natural language summary

### Architecture

```
User Query
    ↓
LangChain Agent (GPT-4o-mini)
    ↓
Tool Selection:
├─ geocode_location_tool → converts place names to coordinates
├─ sentinel1_download_tool → downloads SAR imagery
└─ sentinel2_download_tool → downloads optical imagery
    ↓
STAC API Search (AWS Element84)
    ↓
Download GeoTIFF files
    ↓
Natural Language Response
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/sentinel-ai-agent.git
cd sentinel-ai-agent
```

Install dependencies:

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
streamlit
openai
langchain
langchain-openai
pystac-client
requests
python-dotenv
geopy
```

Set up environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

---

## Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Chat Agent Mode

Type natural language requests like:

**English:**
- "Download Sentinel-2 data near Gwangan Bridge, Busan from June 2023"
- "Get Sentinel-1 SAR imagery for Tokyo Tower on 2024-03-15"
- "I need optical imagery of Jeju Island from last summer"

**Korean:**
- "부산 광안대교 부근 2023년 6월 1일 Sentinel-2 내려줘"
- "서울 강남역 근처 2024년 5월 SAR 영상 필요해"
- "제주도 성산일출봉 2023년 여름 광학 영상 다운로드"

**Place name examples that work:**
- Landmarks: "부산 광안대교", "Tokyo Tower", "Eiffel Tower"
- Stations: "서울 강남역", "Shibuya Station"
- Cities: "Busan", "제주도", "Paris"
- Addresses: "대한민국 부산광역시 수영구"

### Direct Download Mode

Manually input:
- Latitude and longitude coordinates
- Target date
- Search range (±days)
- Cloud cover threshold (Sentinel-2 only)

Choose between Sentinel-1 (SAR) or Sentinel-2 (Optical) tabs

---

## Configuration

### Default Settings

**Search Parameters:**
- Temporal range: ±10 days from target date
- Spatial range: ±0.2° (~22km) from target coordinates
- Cloud cover limit: <20% (Sentinel-2 only)

**Model:**
- LLM: GPT-4o-mini (OpenAI)
- Temperature: 0 (deterministic)

**Data Sources:**
- STAC API: AWS Element84 (https://earth-search.aws.element84.com/v1)
- Collections: sentinel-1-grd, sentinel-2-l2a

### Environment Variables

Create a `.env` file:

```bash
OPENAI_API_KEY=your_openai_api_key
```

Optional: Modify `SAVE_DIR` in `app.py` to change download location (default: project directory)

---

## Data Information

### Sentinel-1 GRD (Ground Range Detected)

- **Sensor**: C-band SAR (5.405 GHz)
- **Spatial resolution**: 10m × 10m
- **Polarization**: VV, VH (or HH, HV depending on region)
- **Revisit time**: 6 days (Sentinel-1A/B combined)
- **Scene size**: ~250km × 170km
- **Weather**: All-weather capable (penetrates clouds)
- **Data format**: GeoTIFF
- **Use cases**: Flood monitoring, deformation analysis, ice monitoring

### Sentinel-2 L2A (Bottom-of-Atmosphere)

- **Sensor**: Multispectral optical (13 bands)
- **Spatial resolution**: 10m (RGB, NIR), 20m (Red Edge, SWIR), 60m (Coastal, Cirrus)
- **Bands downloaded**: Red, Green, Blue, Visual (True Color)
- **Revisit time**: 5 days (Sentinel-2A/B combined)
- **Scene size**: ~110km × 110km (tiled)
- **Weather**: Requires clear skies (cloud filtering applied)
- **Data format**: GeoTIFF
- **Processing**: Atmospherically corrected
- **Use cases**: Land cover classification, vegetation monitoring, water quality

### Data Provider

- **Source**: ESA Copernicus Programme
- **License**: Free and open (CC BY-SA 3.0 IGO)
- **Access**: AWS Open Data Program via Element84 STAC

---

## Example Queries

### Location-based Queries (Geocoding)

**Landmarks:**
```
"Download Sentinel-2 near 부산 광안대교 on 2023-06-01"
"Get SAR data for Tokyo Tower from March 2024"
```

**Cities & Regions:**
```
"서울 근처 2024년 5월 28일 Sentinel-1 내려줘"
"Jeju Island optical imagery from summer 2023"
"Paris, France Sentinel-2 data 2024-01-15"
```

**Addresses:**
```
"대한민국 부산광역시 수영구 광안2동 Sentinel-2 2023년 6월"
"1-1-1 Shibuya, Tokyo Sentinel-1 2024-03-01"
```

### Coordinate-based Queries

```
"Sentinel-1 at coordinates 37.5665, 126.9780 from May 2024"
"Get optical imagery for lat 35.1796, lon 129.0750 on 2023-06-01"
```

### Natural Language Variations

```
"부산 해운대 근처 지난달 위성 영상 필요해"
"I need recent SAR imagery of San Francisco"
"제주도 성산일출봉 2023년 여름 광학 영상"
"Download latest Sentinel-2 for New York City"
```

---

## Project Structure

```
sentinel-ai-agent/
├── app.py                 # Streamlit UI and agent orchestration
├── satellite_tools.py     # Download functions and LangChain tools
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── .env.example          # Environment variable template
├── downloads/            # Default download directory (auto-created)
└── README.md            # This file
```

---

## Troubleshooting

### Common Issues

**"No scenes found":**
- Try increasing the date range (default ±10 days)
- Check if the location is over water/ocean (satellites may not cover)
- For Sentinel-2, try increasing cloud cover threshold

**Location not found:**
- Use more specific names: "부산 광안대교" instead of just "광안대교"
- Try adding country/city: "Gwangan Bridge, Busan, South Korea"
- Alternative: Use direct coordinates in Direct Download mode

**Slow downloads:**
- Sentinel-1 files are large (~1-3 GB per polarization)
- Sentinel-2 RGB files are smaller (~100-500 MB each)
- Download time depends on internet connection

**API Rate Limits:**
- Free tier OpenAI API has rate limits
- Consider upgrading OpenAI plan for heavy usage
- Geopy Nominatim has 1 request/second limit

---

## Limitations

- **Geocoding**: Nominatim (OpenStreetMap) may not recognize very obscure locations
- **Cloud Cover**: Sentinel-2 optical imagery requires clear skies
- **Scene Size**: Downloads entire satellite scenes, not cropped to exact location
- **Historical Data**: Sentinel-1 available from 2014, Sentinel-2 from 2015
- **Processing**: Downloads raw GeoTIFF, additional processing needed for analysis

---

## Future Enhancements

- [ ] Add Sentinel-2 L1C support for wider scene coverage
- [ ] Implement automatic GeoTIFF cropping to region of interest
- [ ] Add support for Landsat-8/9 imagery
- [ ] Include data visualization (thumbnail generation)
- [ ] Add batch download for multiple dates/locations
- [ ] Support for other STAC catalogs (Microsoft Planetary Computer, etc.)
- [ ] Integration with Google Maps API for better geocoding
- [ ] Export metadata to CSV/JSON

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **LangChain** - LLM application framework
- **Streamlit** - Web app framework for rapid prototyping
- **OpenAI** - GPT-4o-mini language model
- **Element84** - STAC API provider and AWS hosting
- **ESA Copernicus** - Sentinel-1 and Sentinel-2 data provider
- **geopy** - Geocoding library for location services
- **OpenStreetMap/Nominatim** - Free geocoding service

---

## Citation

If you use this project in your research, please cite:

```bibtex
@software{sentinel_ai_agent,
  title = {Sentinel AI Agent: Natural Language Satellite Data Download},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/sentinel-ai-agent}
}
```

---

## Contact

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

## Disclaimer

This tool is for research and educational purposes. Users are responsible for complying with data usage policies and terms of service of all data providers. The authors are not responsible for any misuse of downloaded satellite imagery.
