"""
Irrigation Agronomic Service (FAO-56 CROPWAT compliant calculations)
Calculates Crop Evapotranspiration (ETc), Effective Rainfall, Soil Water Depletion,
Net & Gross Irrigation Requirements, and final required volume in Litres.

Crop Kc values sourced from:
  - FAO Irrigation and Drainage Paper No. 56 (Allen et al., 1998), Table 12 & Appendix
  - ICAR Crop Production Guides (India)
  - FAOSTAT crop-specific guidance notes
  - ICRISAT semi-arid crop guidelines

Parameters marked [FAO-56] are directly from FAO-56 Table 12.
Parameters marked [FAO-56 EST] are interpolated/estimated from adjacent FAO-56 entries.
Parameters marked [ICAR] are from ICAR national guides for India.
Parameters marked [NEEDS CALIBRATION] lack authoritative published values and use
  conservative FAO-56 fallback ranges; they should be calibrated with local field data.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta

# Exact 34 crops present in the trained ML benchmark & preprocessor.joblib
ML_TRAINED_CROPS = frozenset({
    "Banana", "Barley", "Black Gram", "Brinjal", "Cabbage", "Carrot",
    "Cauliflower", "Chickpea", "Chilli", "Cotton", "Field Pea",
    "Finger Millet (Ragi)", "Grapes", "Green Gram", "Groundnut", "Lentil",
    "Maize", "Mango", "Mustard", "Onion", "Papaya",
    "Pearl Millet (Bajra)", "Pigeon Pea (Toor Dal)", "Pomegranate", "Potato",
    "Rice (Paddy)", "Sorghum (Jowar)", "Soybean", "Sugarcane", "Sunflower",
    "Tobacco", "Tomato", "Watermelon", "Wheat",
})


CROP_DATABASE: Dict[str, Dict[str, Any]] = {

    # ═══════════════════════════════════════════════════════════════
    # A. CEREALS AND MILLETS
    # ═══════════════════════════════════════════════════════════════

    "Wheat": {
        "category": "Cereals and Millets",
        "scientific_name": "Triticum aestivum",
        "kc_initial": 0.35,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.40,        # [FAO-56] Table 12
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 130,
        "notes": "Winter/Spring wheat. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Rice (Paddy)": {
        "category": "Cereals and Millets",
        "scientific_name": "Oryza sativa",
        "kc_initial": 1.05,     # [FAO-56] Table 12 (flooded paddy)
        "kc_vegetative": 1.10,
        "kc_mid": 1.20,         # [FAO-56] Table 12
        "kc_late": 0.90,        # [FAO-56] Table 12
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.20,
        "typical_yield_season_days": 120,
        "notes": "Lowland flooded paddy. High Kc due to open water surface evaporation.",
        "data_source": "FAO-56"
    },
    "Maize": {
        "category": "Cereals and Millets",
        "scientific_name": "Zea mays",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.80,
        "kc_mid": 1.20,         # [FAO-56] Table 12
        "kc_late": 0.60,        # [FAO-56] Table 12
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 110,
        "notes": "Field corn / grain maize. Also covers sweet corn at similar Kc.",
        "data_source": "FAO-56"
    },
    "Barley": {
        "category": "Cereals and Millets",
        "scientific_name": "Hordeum vulgare",
        "kc_initial": 0.30,     # [FAO-56] Table 12
        "kc_vegetative": 0.70,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.25,        # [FAO-56] Table 12
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 120,
        "notes": "Spring and winter barley.",
        "data_source": "FAO-56"
    },
    "Oats": {
        "category": "Cereals and Millets",
        "scientific_name": "Avena sativa",
        "kc_initial": 0.30,     # [FAO-56 EST] similar to barley
        "kc_vegetative": 0.70,
        "kc_mid": 1.15,         # [FAO-56 EST]
        "kc_late": 0.30,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 120,
        "notes": "Oat grain crop; Kc estimated from FAO-56 small grain cereals.",
        "data_source": "FAO-56 EST"
    },
    "Sorghum (Jowar)": {
        "category": "Cereals and Millets",
        "scientific_name": "Sorghum bicolor",
        "kc_initial": 0.35,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,         # [FAO-56] Table 12
        "kc_late": 0.55,        # [FAO-56] Table 12
        "root_depth_meters": 1.4,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 115,
        "notes": "Grain sorghum / Jowar. Drought-tolerant cereal.",
        "data_source": "FAO-56"
    },
    "Pearl Millet (Bajra)": {
        "category": "Cereals and Millets",
        "scientific_name": "Pennisetum glaucum",
        "kc_initial": 0.35,     # [ICAR] / [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,         # [ICAR]
        "kc_late": 0.45,
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.60,
        "typical_yield_season_days": 90,
        "notes": "Bajra; major dryland cereal of India. ICAR Kc values.",
        "data_source": "ICAR"
    },
    "Finger Millet (Ragi)": {
        "category": "Cereals and Millets",
        "scientific_name": "Eleusine coracana",
        "kc_initial": 0.35,     # [ICAR]
        "kc_vegetative": 0.70,
        "kc_mid": 1.05,         # [ICAR]
        "kc_late": 0.50,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 110,
        "notes": "Ragi / Nachni. ICAR crop guide.",
        "data_source": "ICAR"
    },
    "Foxtail Millet": {
        "category": "Cereals and Millets",
        "scientific_name": "Setaria italica",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.45,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 85,
        "notes": "Kangni / Kakum. Kc values estimated from FAO-56 millet group; local calibration recommended.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Kodo Millet": {
        "category": "Cereals and Millets",
        "scientific_name": "Paspalum scrobiculatum",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.45,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 90,
        "notes": "Minor millet of Central India. Kc values estimated; local calibration recommended.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Barnyard Millet": {
        "category": "Cereals and Millets",
        "scientific_name": "Echinochloa frumentacea",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.45,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 75,
        "notes": "Sanwa / Bhagar. Very short season. Kc estimated from millet group.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Little Millet": {
        "category": "Cereals and Millets",
        "scientific_name": "Panicum sumatrense",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.45,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 85,
        "notes": "Kutki. Kc estimated from FAO-56 millet group.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Proso Millet": {
        "category": "Cereals and Millets",
        "scientific_name": "Panicum miliaceum",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.45,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 75,
        "notes": "Common millet / Cheena. Kc estimated from FAO-56 millet group.",
        "data_source": "NEEDS CALIBRATION"
    },

    # ═══════════════════════════════════════════════════════════════
    # B. PULSES AND LEGUMES
    # ═══════════════════════════════════════════════════════════════

    "Chickpea": {
        "category": "Pulses and Legumes",
        "scientific_name": "Cicer arietinum",
        "kc_initial": 0.40,     # [FAO-56 EST] / [ICAR]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,         # [ICAR]
        "kc_late": 0.35,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 110,
        "notes": "Bengal gram / Chana. Rabi crop in India. ICAR guide values.",
        "data_source": "ICAR"
    },
    "Pigeon Pea (Toor Dal)": {
        "category": "Pulses and Legumes",
        "scientific_name": "Cajanus cajan",
        "kc_initial": 0.35,     # [ICAR]
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,         # [ICAR]
        "kc_late": 0.45,
        "root_depth_meters": 1.3,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 160,
        "notes": "Arhar / Tur. Deep-rooted drought-tolerant legume. ICAR.",
        "data_source": "ICAR"
    },
    "Green Gram": {
        "category": "Pulses and Legumes",
        "scientific_name": "Vigna radiata",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.05,         # [FAO-56 EST] / [ICAR]
        "kc_late": 0.35,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 70,
        "notes": "Moong / Mung bean. Short-season summer pulse.",
        "data_source": "FAO-56 EST"
    },
    "Black Gram": {
        "category": "Pulses and Legumes",
        "scientific_name": "Vigna mungo",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.05,         # [FAO-56 EST]
        "kc_late": 0.35,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 75,
        "notes": "Urad dal. Similar Kc to green gram.",
        "data_source": "FAO-56 EST"
    },
    "Lentil": {
        "category": "Pulses and Legumes",
        "scientific_name": "Lens culinaris",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.70,
        "kc_mid": 1.10,         # [FAO-56] Table 12
        "kc_late": 0.30,        # [FAO-56] Table 12
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 110,
        "notes": "Masoor dal. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Field Pea": {
        "category": "Pulses and Legumes",
        "scientific_name": "Pisum sativum",
        "kc_initial": 0.45,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.30,        # [FAO-56] Table 12
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 95,
        "notes": "Dry pea / matar. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Cowpea": {
        "category": "Pulses and Legumes",
        "scientific_name": "Vigna unguiculata",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.05,         # [FAO-56 EST]
        "kc_late": 0.40,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 90,
        "notes": "Lobia / black-eyed pea. Kc estimated from FAO-56 bean/legume group.",
        "data_source": "FAO-56 EST"
    },
    "Horse Gram": {
        "category": "Pulses and Legumes",
        "scientific_name": "Macrotyloma uniflorum",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.65,
        "kc_mid": 1.00,
        "kc_late": 0.40,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 100,
        "notes": "Kulith / Hurali. Dryland legume. Kc values need local field calibration.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Moth Bean": {
        "category": "Pulses and Legumes",
        "scientific_name": "Vigna aconitifolia",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.65,
        "kc_mid": 1.00,
        "kc_late": 0.40,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.60,
        "typical_yield_season_days": 90,
        "notes": "Mat bean / Dew bean. Arid/semi-arid crop. Kc needs calibration.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Kidney Bean": {
        "category": "Pulses and Legumes",
        "scientific_name": "Phaseolus vulgaris",
        "kc_initial": 0.40,     # [FAO-56] Table 12 (dry bean)
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.35,        # [FAO-56] Table 12
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 95,
        "notes": "Rajma / common bean. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Soybean": {
        "category": "Pulses and Legumes",
        "scientific_name": "Glycine max",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.50,        # [FAO-56] Table 12
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 115,
        "notes": "Soyabean. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Groundnut": {
        "category": "Pulses and Legumes",
        "scientific_name": "Arachis hypogaea",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.60,        # [FAO-56] Table 12
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 120,
        "notes": "Peanut / Moongphali. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },

    # ═══════════════════════════════════════════════════════════════
    # C. OILSEED CROPS
    # ═══════════════════════════════════════════════════════════════

    "Mustard": {
        "category": "Oilseed Crops",
        "scientific_name": "Brassica juncea",
        "kc_initial": 0.35,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.10,         # [FAO-56 EST]
        "kc_late": 0.35,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 105,
        "notes": "Indian mustard / Sarson. Rabi oilseed. Kc estimated from Brassica species.",
        "data_source": "FAO-56 EST"
    },
    "Rapeseed": {
        "category": "Oilseed Crops",
        "scientific_name": "Brassica napus",
        "kc_initial": 0.35,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.10,
        "kc_late": 0.35,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 115,
        "notes": "Canola / Rapeseed. Similar Kc to mustard.",
        "data_source": "FAO-56 EST"
    },
    "Sunflower": {
        "category": "Oilseed Crops",
        "scientific_name": "Helianthus annuus",
        "kc_initial": 0.35,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.40,        # [FAO-56] Table 12
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 100,
        "notes": "Surajmukhi. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Sesame": {
        "category": "Oilseed Crops",
        "scientific_name": "Sesamum indicum",
        "kc_initial": 0.35,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.10,
        "kc_late": 0.50,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.60,
        "typical_yield_season_days": 90,
        "notes": "Til / Gingelly. Kc estimated from FAO-56 oilseeds group.",
        "data_source": "FAO-56 EST"
    },
    "Castor": {
        "category": "Oilseed Crops",
        "scientific_name": "Ricinus communis",
        "kc_initial": 0.35,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,
        "kc_late": 0.55,
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 150,
        "notes": "Arandi. Drought-tolerant. Kc estimated from oilseed crops.",
        "data_source": "FAO-56 EST"
    },
    "Linseed": {
        "category": "Oilseed Crops",
        "scientific_name": "Linum usitatissimum",
        "kc_initial": 0.35,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.10,
        "kc_late": 0.35,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 120,
        "notes": "Flaxseed / Alsi. Kc estimated from FAO-56 oilseed group.",
        "data_source": "FAO-56 EST"
    },
    "Safflower": {
        "category": "Oilseed Crops",
        "scientific_name": "Carthamus tinctorius",
        "kc_initial": 0.35,     # [FAO-56] Table 12
        "kc_vegetative": 0.70,
        "kc_mid": 1.10,         # [FAO-56] Table 12
        "kc_late": 0.40,        # [FAO-56] Table 12
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.60,
        "typical_yield_season_days": 130,
        "notes": "Kusum. Drought-tolerant oilseed. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Niger Seed": {
        "category": "Oilseed Crops",
        "scientific_name": "Guizotia abyssinica",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.70,
        "kc_mid": 1.05,
        "kc_late": 0.40,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 100,
        "notes": "Ramtil. Rainfed tribal belt crop. Kc values need local calibration.",
        "data_source": "NEEDS CALIBRATION"
    },

    # ═══════════════════════════════════════════════════════════════
    # D. COMMERCIAL AND FIBRE CROPS
    # ═══════════════════════════════════════════════════════════════

    "Cotton": {
        "category": "Commercial and Fibre Crops",
        "scientific_name": "Gossypium hirsutum",
        "kc_initial": 0.35,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.20,         # [FAO-56] Table 12
        "kc_late": 0.65,        # [FAO-56] Table 12
        "root_depth_meters": 1.4,
        "critical_depletion_fraction": 0.65,
        "typical_yield_season_days": 180,
        "notes": "American cotton / Kapas. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Sugarcane": {
        "category": "Commercial and Fibre Crops",
        "scientific_name": "Saccharum officinarum",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.85,
        "kc_mid": 1.25,         # [FAO-56] Table 12
        "kc_late": 0.75,        # [FAO-56] Table 12
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.65,
        "typical_yield_season_days": 360,
        "notes": "Ganna. Very long season crop. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Sugar Beet": {
        "category": "Commercial and Fibre Crops",
        "scientific_name": "Beta vulgaris",
        "kc_initial": 0.35,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.20,         # [FAO-56] Table 12
        "kc_late": 0.70,        # [FAO-56] Table 12
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 160,
        "notes": "FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Tobacco": {
        "category": "Commercial and Fibre Crops",
        "scientific_name": "Nicotiana tabacum",
        "kc_initial": 0.35,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.80,        # [FAO-56] Table 12
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 120,
        "notes": "Tambakhu. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Jute": {
        "category": "Commercial and Fibre Crops",
        "scientific_name": "Corchorus capsularis",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,
        "kc_late": 0.70,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 120,
        "notes": "Pat / Golden fibre. Kharif fibre crop. Kc estimated.",
        "data_source": "FAO-56 EST"
    },
    "Kenaf": {
        "category": "Commercial and Fibre Crops",
        "scientific_name": "Hibiscus cannabinus",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.75,
        "kc_mid": 1.10,
        "kc_late": 0.65,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 130,
        "notes": "Deccan hemp / Ambadi. Kc values estimated; calibration recommended.",
        "data_source": "NEEDS CALIBRATION"
    },

    # ═══════════════════════════════════════════════════════════════
    # E. VEGETABLES
    # ═══════════════════════════════════════════════════════════════

    "Tomato": {
        "category": "Vegetables",
        "scientific_name": "Solanum lycopersicum",
        "kc_initial": 0.45,     # [FAO-56] Table 12
        "kc_vegetative": 0.80,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.80,        # [FAO-56] Table 12
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 105,
        "notes": "Fresh market tomato. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Potato": {
        "category": "Vegetables",
        "scientific_name": "Solanum tuberosum",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.75,        # [FAO-56] Table 12
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 100,
        "notes": "Aalu. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Onion": {
        "category": "Vegetables",
        "scientific_name": "Allium cepa",
        "kc_initial": 0.50,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,         # [FAO-56] Table 12
        "kc_late": 0.85,        # [FAO-56] Table 12
        "root_depth_meters": 0.4,
        "critical_depletion_fraction": 0.30,
        "typical_yield_season_days": 95,
        "notes": "Pyaz / Kanda. Shallow root. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Garlic": {
        "category": "Vegetables",
        "scientific_name": "Allium sativum",
        "kc_initial": 0.50,     # [FAO-56 EST] similar to onion
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,
        "kc_late": 0.80,
        "root_depth_meters": 0.4,
        "critical_depletion_fraction": 0.30,
        "typical_yield_season_days": 150,
        "notes": "Lassan. Kc estimated from onion/bulb crop group.",
        "data_source": "FAO-56 EST"
    },
    "Brinjal": {
        "category": "Vegetables",
        "scientific_name": "Solanum melongena",
        "kc_initial": 0.45,     # [FAO-56 EST]
        "kc_vegetative": 0.80,
        "kc_mid": 1.15,
        "kc_late": 0.85,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 130,
        "notes": "Eggplant / Baingan. Kc estimated from FAO-56 Solanaceae group.",
        "data_source": "FAO-56 EST"
    },
    "Chilli": {
        "category": "Vegetables",
        "scientific_name": "Capsicum annuum",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.10,
        "kc_late": 0.85,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 120,
        "notes": "Mirchi / Hot pepper. Kc estimated from pepper Kc values in FAO-56.",
        "data_source": "FAO-56 EST"
    },
    "Capsicum": {
        "category": "Vegetables",
        "scientific_name": "Capsicum annuum var. grossum",
        "kc_initial": 0.40,     # [FAO-56] Table 12 (pepper)
        "kc_vegetative": 0.75,
        "kc_mid": 1.10,         # [FAO-56] Table 12
        "kc_late": 0.80,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.30,
        "typical_yield_season_days": 120,
        "notes": "Bell pepper / Shimla mirchi. FAO-56 pepper Kc.",
        "data_source": "FAO-56"
    },
    "Cabbage": {
        "category": "Vegetables",
        "scientific_name": "Brassica oleracea var. capitata",
        "kc_initial": 0.45,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,         # [FAO-56] Table 12
        "kc_late": 0.90,        # [FAO-56] Table 12
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 90,
        "notes": "Band gobhi. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Cauliflower": {
        "category": "Vegetables",
        "scientific_name": "Brassica oleracea var. botrytis",
        "kc_initial": 0.45,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,
        "kc_late": 0.90,
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 90,
        "notes": "Phool gobhi. Similar to cabbage Kc.",
        "data_source": "FAO-56 EST"
    },
    "Broccoli": {
        "category": "Vegetables",
        "scientific_name": "Brassica oleracea var. italica",
        "kc_initial": 0.45,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,
        "kc_late": 0.90,
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 85,
        "notes": "Broccoli. Similar Kc to cauliflower.",
        "data_source": "FAO-56 EST"
    },
    "Carrot": {
        "category": "Vegetables",
        "scientific_name": "Daucus carota",
        "kc_initial": 0.45,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,         # [FAO-56] Table 12
        "kc_late": 0.85,        # [FAO-56] Table 12
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 85,
        "notes": "Gajar. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Radish": {
        "category": "Vegetables",
        "scientific_name": "Raphanus sativus",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 0.95,
        "kc_late": 0.85,
        "root_depth_meters": 0.4,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 45,
        "notes": "Mooli. Very short season root vegetable. Kc estimated.",
        "data_source": "FAO-56 EST"
    },
    "Beetroot": {
        "category": "Vegetables",
        "scientific_name": "Beta vulgaris var. conditiva",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,
        "kc_late": 0.80,
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 70,
        "notes": "Chukander. Kc estimated from beet/root vegetable group.",
        "data_source": "FAO-56 EST"
    },
    "Spinach": {
        "category": "Vegetables",
        "scientific_name": "Spinacia oleracea",
        "kc_initial": 0.70,     # [FAO-56] Table 12
        "kc_vegetative": 0.80,
        "kc_mid": 1.00,         # [FAO-56] Table 12
        "kc_late": 0.95,
        "root_depth_meters": 0.3,
        "critical_depletion_fraction": 0.20,
        "typical_yield_season_days": 50,
        "notes": "Palak. High Kc due to full ground cover and shallow root. FAO-56.",
        "data_source": "FAO-56"
    },
    "Lettuce": {
        "category": "Vegetables",
        "scientific_name": "Lactuca sativa",
        "kc_initial": 0.70,     # [FAO-56] Table 12
        "kc_vegetative": 0.85,
        "kc_mid": 1.00,         # [FAO-56] Table 12
        "kc_late": 0.95,
        "root_depth_meters": 0.3,
        "critical_depletion_fraction": 0.30,
        "typical_yield_season_days": 55,
        "notes": "Salad crop. Very shallow roots. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Cucumber": {
        "category": "Vegetables",
        "scientific_name": "Cucumis sativus",
        "kc_initial": 0.45,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,         # [FAO-56] Table 12
        "kc_late": 0.75,        # [FAO-56] Table 12
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 70,
        "notes": "Kheera / Kakdi. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Pumpkin": {
        "category": "Vegetables",
        "scientific_name": "Cucurbita moschata",
        "kc_initial": 0.45,     # [FAO-56 EST] cucurbits group
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,
        "kc_late": 0.75,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 90,
        "notes": "Kaddu / Sitaphal. Kc estimated from FAO-56 squash/pumpkin.",
        "data_source": "FAO-56 EST"
    },
    "Bottle Gourd": {
        "category": "Vegetables",
        "scientific_name": "Lagenaria siceraria",
        "kc_initial": 0.45,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,
        "kc_late": 0.75,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 90,
        "notes": "Lauki / Ghia. Kc estimated from cucurbit group.",
        "data_source": "FAO-56 EST"
    },
    "Bitter Gourd": {
        "category": "Vegetables",
        "scientific_name": "Momordica charantia",
        "kc_initial": 0.45,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,
        "kc_late": 0.75,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 85,
        "notes": "Karela. Kc estimated from cucurbit group.",
        "data_source": "FAO-56 EST"
    },
    "Ridge Gourd": {
        "category": "Vegetables",
        "scientific_name": "Luffa acutangula",
        "kc_initial": 0.45,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,
        "kc_late": 0.75,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 85,
        "notes": "Turai / Jhinga. Kc needs field calibration.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Okra": {
        "category": "Vegetables",
        "scientific_name": "Abelmoschus esculentus",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,
        "kc_late": 0.85,
        "root_depth_meters": 0.7,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 90,
        "notes": "Bhindi / Lady's finger. Kc estimated from tropical vegetables.",
        "data_source": "FAO-56 EST"
    },
    "Sweet Corn": {
        "category": "Vegetables",
        "scientific_name": "Zea mays var. saccharata",
        "kc_initial": 0.40,     # [FAO-56] Table 12 (corn/maize group)
        "kc_vegetative": 0.80,
        "kc_mid": 1.15,
        "kc_late": 1.05,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 85,
        "notes": "Fresh-eating corn. Higher late-Kc than field corn due to harvest at milk stage.",
        "data_source": "FAO-56 EST"
    },
    "Sweet Potato": {
        "category": "Vegetables",
        "scientific_name": "Ipomoea batatas",
        "kc_initial": 0.50,     # [FAO-56] Table 12
        "kc_vegetative": 0.80,
        "kc_mid": 1.15,         # [FAO-56] Table 12
        "kc_late": 0.65,        # [FAO-56] Table 12
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.65,
        "typical_yield_season_days": 120,
        "notes": "Shakarkand. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Cassava": {
        "category": "Vegetables",
        "scientific_name": "Manihot esculenta",
        "kc_initial": 0.30,     # [FAO-56] Table 12
        "kc_vegetative": 0.60,
        "kc_mid": 0.80,         # [FAO-56] Table 12
        "kc_late": 0.60,        # [FAO-56] Table 12
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.65,
        "typical_yield_season_days": 300,
        "notes": "Tapioca / Manioc / Kappa. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },

    # ═══════════════════════════════════════════════════════════════
    # F. FRUITS
    # ═══════════════════════════════════════════════════════════════

    "Mango": {
        "category": "Fruits",
        "scientific_name": "Mangifera indica",
        "kc_initial": 0.55,     # [FAO-56 EST] tropical tree fruit
        "kc_vegetative": 0.75,
        "kc_mid": 0.90,
        "kc_late": 0.70,
        "root_depth_meters": 1.8,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 365,
        "notes": "Aam. Perennial tree. Kc varies by bearing age and canopy cover.",
        "data_source": "FAO-56 EST"
    },
    "Banana": {
        "category": "Fruits",
        "scientific_name": "Musa spp.",
        "kc_initial": 0.50,     # [FAO-56] Table 12
        "kc_vegetative": 0.90,
        "kc_mid": 1.20,         # [FAO-56] Table 12
        "kc_late": 1.10,        # [FAO-56] Table 12
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 330,
        "notes": "Kela. High water demand. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Papaya": {
        "category": "Fruits",
        "scientific_name": "Carica papaya",
        "kc_initial": 0.50,     # [FAO-56 EST]
        "kc_vegetative": 0.85,
        "kc_mid": 1.10,
        "kc_late": 0.90,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 300,
        "notes": "Papita. Tropical fruit tree. Kc estimated from tropical fruit.",
        "data_source": "FAO-56 EST"
    },
    "Guava": {
        "category": "Fruits",
        "scientific_name": "Psidium guajava",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 0.85,
        "kc_late": 0.65,
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 365,
        "notes": "Amrud. Drought-tolerant perennial. Kc estimated.",
        "data_source": "FAO-56 EST"
    },
    "Pomegranate": {
        "category": "Fruits",
        "scientific_name": "Punica granatum",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.65,
        "kc_mid": 0.85,
        "kc_late": 0.55,
        "root_depth_meters": 1.4,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 240,
        "notes": "Anar. Semi-arid fruit. Kc estimated from deciduous fruit tree group.",
        "data_source": "FAO-56 EST"
    },
    "Grapes": {
        "category": "Fruits",
        "scientific_name": "Vitis vinifera",
        "kc_initial": 0.30,     # [FAO-56] Table 12
        "kc_vegetative": 0.60,
        "kc_mid": 0.85,         # [FAO-56] Table 12
        "kc_late": 0.45,        # [FAO-56] Table 12
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 210,
        "notes": "Angur. Table & wine grapes. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Orange": {
        "category": "Fruits",
        "scientific_name": "Citrus sinensis",
        "kc_initial": 0.65,     # [FAO-56] Table 12 (citrus with active ground cover)
        "kc_vegetative": 0.75,
        "kc_mid": 0.70,         # [FAO-56] Table 12
        "kc_late": 0.65,
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 365,
        "notes": "Santra / Narangi. FAO-56 citrus Table 12.",
        "data_source": "FAO-56"
    },
    "Lemon": {
        "category": "Fruits",
        "scientific_name": "Citrus limon",
        "kc_initial": 0.65,     # [FAO-56 EST] citrus group
        "kc_vegetative": 0.75,
        "kc_mid": 0.70,
        "kc_late": 0.65,
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 365,
        "notes": "Nimbu. Citrus Kc from FAO-56.",
        "data_source": "FAO-56 EST"
    },
    "Watermelon": {
        "category": "Fruits",
        "scientific_name": "Citrullus lanatus",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,         # [FAO-56] Table 12
        "kc_late": 0.75,        # [FAO-56] Table 12
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 85,
        "notes": "Tarbuj. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Muskmelon": {
        "category": "Fruits",
        "scientific_name": "Cucumis melo",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,
        "kc_late": 0.75,
        "root_depth_meters": 0.8,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 90,
        "notes": "Kharbuja. Cucurbit similar to watermelon.",
        "data_source": "FAO-56 EST"
    },
    "Pineapple": {
        "category": "Fruits",
        "scientific_name": "Ananas comosus",
        "kc_initial": 0.50,     # [FAO-56] Table 12
        "kc_vegetative": 0.60,
        "kc_mid": 0.60,         # [FAO-56] Table 12 (mulched)
        "kc_late": 0.60,
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 365,
        "notes": "Ananas. Low Kc due to CAM metabolism. FAO-56.",
        "data_source": "FAO-56"
    },
    "Strawberry": {
        "category": "Fruits",
        "scientific_name": "Fragaria × ananassa",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.70,
        "kc_mid": 0.85,         # [FAO-56] Table 12
        "kc_late": 0.75,        # [FAO-56] Table 12
        "root_depth_meters": 0.3,
        "critical_depletion_fraction": 0.20,
        "typical_yield_season_days": 150,
        "notes": "Strawberry. Very shallow roots. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Coconut": {
        "category": "Fruits",
        "scientific_name": "Cocos nucifera",
        "kc_initial": 0.90,     # [FAO-56 EST] tall palm
        "kc_vegetative": 1.00,
        "kc_mid": 1.00,
        "kc_late": 1.00,
        "root_depth_meters": 2.0,
        "critical_depletion_fraction": 0.65,
        "typical_yield_season_days": 365,
        "notes": "Nariyal. Evergreen palm. High year-round water demand. Kc estimated.",
        "data_source": "FAO-56 EST"
    },
    "Avocado": {
        "category": "Fruits",
        "scientific_name": "Persea americana",
        "kc_initial": 0.65,     # [FAO-56 EST]
        "kc_vegetative": 0.80,
        "kc_mid": 0.85,
        "kc_late": 0.70,
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.70,
        "typical_yield_season_days": 365,
        "notes": "Makhanphal. Subtropical fruit. Kc estimated from tropical tree fruit.",
        "data_source": "FAO-56 EST"
    },

    # ═══════════════════════════════════════════════════════════════
    # G. PLANTATION AND SPICE CROPS
    # ═══════════════════════════════════════════════════════════════

    "Coffee": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Coffea arabica / C. canephora",
        "kc_initial": 0.90,     # [FAO-56 EST] perennial shade crop
        "kc_vegetative": 1.00,
        "kc_mid": 1.05,
        "kc_late": 1.00,
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 365,
        "notes": "Arabica/Robusta coffee. Perennial plantation. Kc estimated from evergreen tree crop.",
        "data_source": "FAO-56 EST"
    },
    "Tea": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Camellia sinensis",
        "kc_initial": 1.00,     # [FAO-56 EST]
        "kc_vegetative": 1.05,
        "kc_mid": 1.10,
        "kc_late": 1.00,
        "root_depth_meters": 1.2,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 365,
        "notes": "Chai. High water demand plantation crop in humid climate.",
        "data_source": "FAO-56 EST"
    },
    "Ginger": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Zingiber officinale",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.05,
        "kc_late": 0.80,
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 240,
        "notes": "Adrak. Rhizome spice. Kc estimated from tropical root/rhizome crops.",
        "data_source": "FAO-56 EST"
    },
    "Turmeric": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Curcuma longa",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.80,
        "kc_mid": 1.05,
        "kc_late": 0.75,
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 270,
        "notes": "Haldi. Kc estimated similar to ginger rhizome.",
        "data_source": "FAO-56 EST"
    },
    "Black Pepper": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Piper nigrum",
        "kc_initial": 0.70,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.90,
        "kc_mid": 1.00,
        "kc_late": 0.90,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 365,
        "notes": "Kali mirch. Perennial vine. Kc values need regional calibration.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Cardamom": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Elettaria cardamomum",
        "kc_initial": 0.70,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.90,
        "kc_mid": 1.05,
        "kc_late": 0.95,
        "root_depth_meters": 1.0,
        "critical_depletion_fraction": 0.30,
        "typical_yield_season_days": 365,
        "notes": "Elaichi. High humidity shaded crop. Kc needs calibration.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Coriander": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Coriandrum sativum",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.75,
        "root_depth_meters": 0.4,
        "critical_depletion_fraction": 0.40,
        "typical_yield_season_days": 90,
        "notes": "Dhania. Seed/herb spice. Kc estimated from small herb crops.",
        "data_source": "FAO-56 EST"
    },
    "Cumin": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Cuminum cyminum",
        "kc_initial": 0.35,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.65,
        "kc_mid": 0.95,
        "kc_late": 0.70,
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 90,
        "notes": "Jeera. Drought-tolerant spice crop. Kc values need field calibration.",
        "data_source": "NEEDS CALIBRATION"
    },
    "Fenugreek": {
        "category": "Plantation and Spice Crops",
        "scientific_name": "Trigonella foenum-graecum",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.70,
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.45,
        "typical_yield_season_days": 90,
        "notes": "Methi. Cool-season spice. Kc estimated from legume/herb group.",
        "data_source": "FAO-56 EST"
    },

    # ═══════════════════════════════════════════════════════════════
    # H. FODDER AND FORAGE CROPS
    # ═══════════════════════════════════════════════════════════════

    "Alfalfa": {
        "category": "Fodder and Forage Crops",
        "scientific_name": "Medicago sativa",
        "kc_initial": 0.40,     # [FAO-56] Table 12
        "kc_vegetative": 0.90,
        "kc_mid": 1.20,         # [FAO-56] Table 12
        "kc_late": 1.15,        # [FAO-56] Table 12 (average over cuttings)
        "root_depth_meters": 2.0,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 365,
        "notes": "Lucerne / Rijka. High water use perennial forage. FAO-56 Table 12.",
        "data_source": "FAO-56"
    },
    "Berseem": {
        "category": "Fodder and Forage Crops",
        "scientific_name": "Trifolium alexandrinum",
        "kc_initial": 0.40,     # [FAO-56 EST] clover group
        "kc_vegetative": 0.90,
        "kc_mid": 1.15,
        "kc_late": 1.10,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.50,
        "typical_yield_season_days": 150,
        "notes": "Egyptian clover / Berseem. Major Rabi fodder in India.",
        "data_source": "FAO-56 EST"
    },
    "Napier Grass": {
        "category": "Fodder and Forage Crops",
        "scientific_name": "Pennisetum purpureum",
        "kc_initial": 0.50,     # [FAO-56 EST] tropical grass
        "kc_vegetative": 0.90,
        "kc_mid": 1.10,
        "kc_late": 1.00,
        "root_depth_meters": 1.5,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 365,
        "notes": "Elephant grass. High biomass tropical fodder. Kc estimated.",
        "data_source": "FAO-56 EST"
    },
    "Fodder Sorghum": {
        "category": "Fodder and Forage Crops",
        "scientific_name": "Sorghum bicolor (fodder types)",
        "kc_initial": 0.35,     # [FAO-56 EST]
        "kc_vegetative": 0.80,
        "kc_mid": 1.10,
        "kc_late": 0.75,
        "root_depth_meters": 1.4,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 90,
        "notes": "Green sorghum fodder. Similar Kc to grain sorghum.",
        "data_source": "FAO-56 EST"
    },

    # ═══════════════════════════════════════════════════════════════
    # I. OTHER AGRICULTURAL CROPS
    # ═══════════════════════════════════════════════════════════════

    "Quinoa": {
        "category": "Other Agricultural Crops",
        "scientific_name": "Chenopodium quinoa",
        "kc_initial": 0.35,     # [FAO-56 EST]
        "kc_vegetative": 0.70,
        "kc_mid": 1.00,
        "kc_late": 0.55,
        "root_depth_meters": 0.9,
        "critical_depletion_fraction": 0.55,
        "typical_yield_season_days": 120,
        "notes": "Pseudo-cereal. Kc estimated from FAO-56 small grain cereals group.",
        "data_source": "FAO-56 EST"
    },
    "Taro": {
        "category": "Other Agricultural Crops",
        "scientific_name": "Colocasia esculenta",
        "kc_initial": 0.40,     # [FAO-56 EST]
        "kc_vegetative": 0.75,
        "kc_mid": 1.00,
        "kc_late": 0.80,
        "root_depth_meters": 0.6,
        "critical_depletion_fraction": 0.30,
        "typical_yield_season_days": 200,
        "notes": "Arabi / Colocasia / Yam. Kc estimated from tropical root crops.",
        "data_source": "FAO-56 EST"
    },
    "Stevia": {
        "category": "Other Agricultural Crops",
        "scientific_name": "Stevia rebaudiana",
        "kc_initial": 0.50,     # [NEEDS CALIBRATION]
        "kc_vegetative": 0.80,
        "kc_mid": 1.00,
        "kc_late": 0.80,
        "root_depth_meters": 0.5,
        "critical_depletion_fraction": 0.35,
        "typical_yield_season_days": 365,
        "notes": "Natural sweetener herb. Very limited published Kc data; local calibration required.",
        "data_source": "NEEDS CALIBRATION"
    },
}


CROP_ALIASES: Dict[str, str] = {
    # Cereals
    "Rice": "Rice (Paddy)",
    "Paddy": "Rice (Paddy)",
    "Corn": "Maize",
    "Sweet Corn": "Sweet Corn",   # separate entry
    "Sorghum": "Sorghum (Jowar)",
    "Jowar": "Sorghum (Jowar)",
    "Pearl Millet": "Pearl Millet (Bajra)",
    "Bajra": "Pearl Millet (Bajra)",
    "Finger Millet": "Finger Millet (Ragi)",
    "Ragi": "Finger Millet (Ragi)",
    "Nachni": "Finger Millet (Ragi)",
    "Foxtail Millet": "Foxtail Millet",
    "Kangni": "Foxtail Millet",
    # Pulses
    "Bengal Gram": "Chickpea",
    "Chana": "Chickpea",
    "Pigeon Pea": "Pigeon Pea (Toor Dal)",
    "Toor Dal": "Pigeon Pea (Toor Dal)",
    "Tur Dal": "Pigeon Pea (Toor Dal)",
    "Arhar": "Pigeon Pea (Toor Dal)",
    "Green Gram (Moong)": "Green Gram",
    "Moong": "Green Gram",
    "Moong Dal": "Green Gram",
    "Mung": "Green Gram",
    "Mung Bean": "Green Gram",
    "Black Gram (Urad)": "Black Gram",
    "Urad": "Black Gram",
    "Urad Dal": "Black Gram",
    "Masoor": "Lentil",
    "Masoor Dal": "Lentil",
    "Rajma": "Kidney Bean",
    "Lobia": "Cowpea",
    "Kulith": "Horse Gram",
    # Oilseeds
    "Rapeseed": "Rapeseed",
    "Canola": "Rapeseed",
    "Sarson": "Mustard",
    "Sesame": "Sesame",
    "Til": "Sesame",
    "Gingelly": "Sesame",
    "Surajmukhi": "Sunflower",
    "Flaxseed": "Linseed",
    "Flax": "Linseed",
    "Alsi": "Linseed",
    # Commercial
    "Sugar Beet": "Sugar Beet",
    "Kapas": "Cotton",
    "Ganna": "Sugarcane",
    "Jute": "Jute",
    # Vegetables
    "Eggplant": "Brinjal",
    "Aubergine": "Brinjal",
    "Baingan": "Brinjal",
    "Green Chilli": "Chilli",
    "Red Chilli": "Chilli",
    "Bell Pepper": "Capsicum",
    "Shimla Mirchi": "Capsicum",
    "Band Gobhi": "Cabbage",
    "Phool Gobhi": "Cauliflower",
    "Gajar": "Carrot",
    "Mooli": "Radish",
    "Chukander": "Beetroot",
    "Palak": "Spinach",
    "Kheera": "Cucumber",
    "Kakdi": "Cucumber",
    "Kaddu": "Pumpkin",
    "Lauki": "Bottle Gourd",
    "Ghia": "Bottle Gourd",
    "Karela": "Bitter Gourd",
    "Bhindi": "Okra",
    "Lady's Finger": "Okra",
    "Ladies Finger": "Okra",
    "Shakarkand": "Sweet Potato",
    "Tapioca": "Cassava",
    "Manioc": "Cassava",
    "Kappa": "Cassava",
    "Yam": "Taro",
    "Colocasia": "Taro",
    "Arabi": "Taro",
    # Fruits
    "Aam": "Mango",
    "Kela": "Banana",
    "Papita": "Papaya",
    "Amrud": "Guava",
    "Anar": "Pomegranate",
    "Grape": "Grapes",
    "Angur": "Grapes",
    "Santra": "Orange",
    "Sweet Lime": "Orange",
    "Lime": "Lemon",
    "Nimbu": "Lemon",
    "Tarbuj": "Watermelon",
    "Kharbuja": "Muskmelon",
    "Cantaloupe": "Muskmelon",
    "Ananas": "Pineapple",
    "Nariyal": "Coconut",
    "Makhanphal": "Avocado",
    # Plantation/Spice
    "Chai": "Tea",
    "Adrak": "Ginger",
    "Haldi": "Turmeric",
    "Kali Mirch": "Black Pepper",
    "Elaichi": "Cardamom",
    "Dhania": "Coriander",
    "Jeera": "Cumin",
    "Methi": "Fenugreek",
    # Fodder
    "Lucerne": "Alfalfa",
    "Rijka": "Alfalfa",
    "Elephant Grass": "Napier Grass",
    # Other
    "Flaxseed": "Linseed",
}


def resolve_crop_name(name: str) -> str:
    """Resolves potential short names or aliases to canonical CROP_DATABASE key."""
    if not name:
        return "Wheat"
    clean = str(name).strip()
    if clean in CROP_DATABASE:
        return clean
    if clean in CROP_ALIASES:
        resolved = CROP_ALIASES[clean]
        if resolved in CROP_DATABASE:
            return resolved
    lower = clean.lower()
    for k in CROP_DATABASE:
        if k.lower() == lower:
            return k
    for alias, target in CROP_ALIASES.items():
        if alias.lower() == lower and target in CROP_DATABASE:
            return target
    # Partial match fallback
    for k in CROP_DATABASE:
        if lower in k.lower() or k.lower() in lower:
            return k
    return "Wheat"


SOIL_DATABASE: Dict[str, Dict[str, Any]] = {
    "Sandy": {
        "field_capacity_pct": 12.0,
        "wilting_point_pct": 5.0,
        "available_water_capacity_mm_per_m": 70.0,
        "infiltration_rate_mm_per_hr": 30.0,
        "description": "Coarse-textured soil with high drainage and low moisture retention."
    },
    "Sandy Loam": {
        "field_capacity_pct": 18.0,
        "wilting_point_pct": 8.0,
        "available_water_capacity_mm_per_m": 100.0,
        "infiltration_rate_mm_per_hr": 20.0,
        "description": "Permeable soil balancing drainage and moisture retention well."
    },
    "Loamy": {
        "field_capacity_pct": 26.0,
        "wilting_point_pct": 12.0,
        "available_water_capacity_mm_per_m": 140.0,
        "infiltration_rate_mm_per_hr": 12.0,
        "description": "Ideal agricultural soil with balanced aeration and high nutrient/moisture capacity."
    },
    "Clay Loam": {
        "field_capacity_pct": 32.0,
        "wilting_point_pct": 18.0,
        "available_water_capacity_mm_per_m": 140.0,
        "infiltration_rate_mm_per_hr": 8.0,
        "description": "Moderately heavy soil with very high water storage capacity."
    },
    "Silty": {
        "field_capacity_pct": 30.0,
        "wilting_point_pct": 14.0,
        "available_water_capacity_mm_per_m": 160.0,
        "infiltration_rate_mm_per_hr": 10.0,
        "description": "Fine-textured fertile soil with high available water content."
    },
    "Clay": {
        "field_capacity_pct": 38.0,
        "wilting_point_pct": 24.0,
        "available_water_capacity_mm_per_m": 140.0,
        "infiltration_rate_mm_per_hr": 4.0,
        "description": "Heavy soil with slow infiltration, prone to waterlogging if over-irrigated."
    }
}

IRRIGATION_METHODS: Dict[str, Dict[str, Any]] = {
    "Drip": {
        "efficiency_pct": 90.0,
        "typical_pressure_bar": 1.5,
        "suitable_crops": ["Tomato", "Potato", "Cotton", "Sugarcane", "Wheat", "Maize", "Soybean"],
        "description": "Micro-irrigation delivering water directly to root zones with minimal evaporative loss (90% efficiency)."
    },
    "Sprinkler": {
        "efficiency_pct": 75.0,
        "typical_pressure_bar": 2.5,
        "suitable_crops": ["Wheat", "Barley", "Maize", "Soybean", "Onion"],
        "description": "Overhead pressurized spray system imitating rainfall (75% efficiency)."
    },
    "Surface/Flood": {
        "efficiency_pct": 60.0,
        "typical_pressure_bar": 0.5,
        "suitable_crops": ["Rice (Paddy)", "Sugarcane", "Wheat"],
        "description": "Gravity flow surface distribution with standard furrow/basin losses (60% efficiency)."
    }
}


def convert_area_to_sq_meters(area: float, unit: str) -> float:
    """Convert input farm area to square meters."""
    unit_lower = unit.lower().strip()
    if unit_lower in ["ha", "hectare", "hectares"]:
        return area * 10000.0
    elif unit_lower in ["ac", "acre", "acres"]:
        return area * 4046.8564224
    elif unit_lower in ["sq_m", "sqm", "sq_meters", "m2", "square_meters"]:
        return area
    return area * 10000.0  # default hectares


def get_crop_kc(crop_name: str, growth_stage: str) -> float:
    """Retrieve Kc coefficient based on crop and growth stage."""
    canonical = resolve_crop_name(crop_name)
    crop = CROP_DATABASE.get(canonical, CROP_DATABASE["Wheat"])

    stage_lower = growth_stage.lower()
    if "init" in stage_lower:
        return crop["kc_initial"]
    elif "mid" in stage_lower or "flower" in stage_lower:
        return crop["kc_mid"]
    elif "late" in stage_lower or "matur" in stage_lower or "harvest" in stage_lower:
        return crop["kc_late"]
    elif "veg" in stage_lower or "develop" in stage_lower or "canopy" in stage_lower:
        return crop.get("kc_vegetative", (crop["kc_initial"] + crop["kc_mid"]) / 2.0)
    else:
        return crop["kc_mid"]


def calculate_effective_rainfall(rainfall_mm: float) -> float:
    """
    FAO/USDA method for effective daily rainfall.
    Small rain showers below 5mm evaporate without contributing to root zone.
    """
    if rainfall_mm <= 5.0:
        return 0.0
    elif rainfall_mm <= 50.0:
        return (rainfall_mm - 5.0) * 0.75
    else:
        return (45.0 * 0.75) + ((rainfall_mm - 50.0) * 0.50)


def calculate_soil_water_balance(
    soil_type: str,
    soil_moisture_pct: float,
    root_depth_m: float,
    critical_depletion_p: float,
    custom_fc: float = None,
    custom_pwp: float = None
) -> Tuple[float, float, float, float]:
    """
    Computes soil moisture metrics:
    - total_available_water_mm (TAW)
    - readily_available_water_mm (RAW)
    - root_zone_depletion_mm (Dr)
    - depletion_fraction
    Supports custom FC and PWP from ISRIC SoilGrids 250m.
    """
    soil = SOIL_DATABASE.get(soil_type, SOIL_DATABASE["Loamy"])
    fc = custom_fc if (custom_fc is not None and custom_fc > 0) else soil["field_capacity_pct"]
    pwp = custom_pwp if (custom_pwp is not None and custom_pwp >= 0) else soil["wilting_point_pct"]
    if pwp >= fc:
        pwp = max(0.0, round(fc * 0.45, 1))

    # TAW in mm = 1000 * (FC - PWP)/100 * Zr
    taw = max(10.0, 10.0 * (fc - pwp) * root_depth_m)
    raw = taw * critical_depletion_p

    # Current moisture relative to FC
    if soil_moisture_pct >= fc:
        depletion_mm = 0.0
    else:
        depletion_mm = min(taw, max(0.0, 10.0 * (fc - soil_moisture_pct) * root_depth_m))

    depletion_fraction = min(1.0, max(0.0, depletion_mm / taw if taw > 0 else 0.0))
    return taw, raw, depletion_mm, depletion_fraction


def calculate_irrigation_recommendation(
    crop_type: str,
    growth_stage: str,
    area: float,
    area_unit: str,
    soil_type: str,
    soil_moisture_pct: float,
    temperature_c: float,
    humidity_pct: float,
    wind_speed_kmh: float,
    rainfall_mm: float,
    reference_et0_mm: float,
    irrigation_method: str = "Drip",
    ml_predicted_mm: float = None,
    custom_fc: float = None,
    custom_pwp: float = None,
    soil_source: str = "manual",
    usda_soil_texture: str = None
) -> Dict[str, Any]:
    """
    Complete FAO-56 Agronomic calculation engine.
    Computes required water depth in mm, converts to total litres for farm area,
    and returns schedule and urgency.
    """
    canonical_crop = resolve_crop_name(crop_type)
    crop = CROP_DATABASE.get(canonical_crop, CROP_DATABASE["Wheat"])
    soil = SOIL_DATABASE.get(soil_type, SOIL_DATABASE["Loamy"])
    irr_info = IRRIGATION_METHODS.get(irrigation_method, IRRIGATION_METHODS["Drip"])

    area_sq_meters = convert_area_to_sq_meters(area, area_unit)
    kc = get_crop_kc(crop_type, growth_stage)
    etc_mm = reference_et0_mm * kc

    peff_mm = calculate_effective_rainfall(rainfall_mm)

    root_depth = crop["root_depth_meters"]
    p_depletion = crop["critical_depletion_fraction"]
    taw, raw, depletion_mm, depletion_fraction = calculate_soil_water_balance(
        soil_type, soil_moisture_pct, root_depth, p_depletion,
        custom_fc=custom_fc, custom_pwp=custom_pwp
    )

    # Net Irrigation Requirement (NIR) in mm/day
    base_nir = max(0.0, etc_mm - peff_mm)
    if depletion_mm > raw:
        # Moisture is depleted past readily available threshold: add depletion replenishment
        base_nir += (depletion_mm - raw) * 0.4

    # Gross Irrigation Requirement (GIR) accounting for application efficiency
    # Note: ml_predicted_mm is trained on gross water_requirement_mm (GIR), so blend at GIR scale
    # to avoid double-dividing by irrigation efficiency. Only blend for crops in ML_TRAINED_CROPS.
    efficiency = irr_info["efficiency_pct"] / 100.0
    base_gir = (base_nir / efficiency) if efficiency > 0 else base_nir
    is_ml_trained_crop = canonical_crop in ML_TRAINED_CROPS

    if ml_predicted_mm is not None and ml_predicted_mm > 0 and is_ml_trained_crop:
        # Blend ML GIR prediction with physical FAO-56 GIR (75% ML, 25% physical balance)
        gir_mm = round(max(0.0, (0.75 * ml_predicted_mm) + (0.25 * base_gir)), 2)
        nir_mm = round(gir_mm * efficiency, 2) if efficiency > 0 else gir_mm
    else:
        nir_mm = base_nir
        gir_mm = round(base_gir, 2)

    # Convert to Litres:
    # 1 mm depth on 1 m2 = 1 Litre
    water_litres = round(gir_mm * area_sq_meters, 2)
    water_m3 = round(water_litres / 1000.0, 3)

    # Urgency & Recommendation logic
    irrigation_recommended = gir_mm > 0.5
    if depletion_mm >= raw * 1.2 or soil_moisture_pct <= (soil["wilting_point_pct"] + 2.0):
        urgency = "Critical"
    elif depletion_mm >= raw or gir_mm >= 6.0:
        urgency = "High"
    elif gir_mm >= 2.5:
        urgency = "Moderate"
    elif gir_mm > 0.5:
        urgency = "Low"
    else:
        urgency = "None"
        irrigation_recommended = False

    # Irrigation Scheduling
    if gir_mm > 0:
        if soil_type in ["Sandy", "Sandy Loam"]:
            freq_days = 1
            duration_hrs = round(min(6.0, max(1.0, (gir_mm / 3.0))), 1)
        elif soil_type in ["Clay", "Clay Loam"]:
            freq_days = 3
            duration_hrs = round(min(8.0, max(1.5, (gir_mm / 2.0))), 1)
        else:
            freq_days = 2
            duration_hrs = round(min(6.0, max(1.0, (gir_mm / 2.5))), 1)
    else:
        freq_days = 0
        duration_hrs = 0.0

    best_time = "Early Morning (5:00 AM - 8:00 AM)" if temperature_c >= 26.0 else "Late Afternoon (4:30 PM - 7:00 PM)"
    next_date = (datetime.now() + timedelta(days=max(1, freq_days) if irrigation_recommended else 2)).strftime("%Y-%m-%d")

    # Generate tailored agronomic tips
    recommendations: List[str] = []
    if irrigation_recommended:
        recommendations.append(
            f"Apply approximately {water_litres:,.0f} litres ({gir_mm:.1f} mm) across {area} {area_unit} using {irrigation_method} irrigation."
        )
        recommendations.append(
            f"Optimal application window: {best_time} to minimize evaporative losses."
        )
        if rainfall_mm > 5:
            recommendations.append(
                f"Recent rainfall of {rainfall_mm:.1f} mm provided {peff_mm:.1f} mm effective moisture, reducing irrigation needs."
            )
        if soil_moisture_pct < soil["wilting_point_pct"] + 4.0:
            recommendations.append(
                f"Soil moisture ({soil_moisture_pct:.1f}%) is nearing wilting point ({soil['wilting_point_pct']}%). Irrigate promptly."
            )
        if temperature_c > 35.0:
            recommendations.append(
                f"Elevated temperatures ({temperature_c:.1f}°C) heighten ETc ({etc_mm:.1f} mm/day). Avoid mid-day water applications."
            )
    else:
        recommendations.append(
            f"Current root zone moisture ({soil_moisture_pct:.1f}%) and weather conditions do not require immediate irrigation."
        )
        recommendations.append(
            f"Next recommended soil moisture inspection on {next_date}."
        )

    if soil_source == "isric_soilgrids_250m" or usda_soil_texture:
        fc_val = custom_fc if custom_fc is not None else soil["field_capacity_pct"]
        pwp_val = custom_pwp if custom_pwp is not None else soil["wilting_point_pct"]
        recommendations.append(
            f"Soil parameters calibrated using ISRIC SoilGrids 250m (USDA texture: {usda_soil_texture or 'Classified'}, FC: {fc_val:.1f}%, PWP: {pwp_val:.1f}%)."
        )

    # Data provenance & ML generalization notices
    crop_data_source = crop.get("data_source", "FAO-56")
    if crop_data_source == "NEEDS CALIBRATION":
        recommendations.append(
            f"Note: {canonical_crop} Kc values are estimated fallbacks. Local field calibration is recommended for precise irrigation scheduling."
        )
    if not is_ml_trained_crop:
        recommendations.append(
            f"ML Generalization Notice: Pre-trained ML models were validated on the original 34-crop benchmark. For {canonical_crop}, water requirement is computed directly using the FAO-56 physical water balance."
        )

    return {
        "crop_type": crop_type,
        "growth_stage": growth_stage,
        "area": area,
        "area_unit": area_unit,
        "area_sq_meters": area_sq_meters,
        "soil_type": soil_type,
        "soil_moisture_pct": soil_moisture_pct,
        "reference_et0_mm": round(reference_et0_mm, 2),
        "crop_kc": round(kc, 3),
        "crop_evapotranspiration_etc_mm": round(etc_mm, 2),
        "effective_rainfall_mm": round(peff_mm, 2),
        "soil_depletion_fraction": round(depletion_fraction, 3),
        "net_irrigation_requirement_mm": round(nir_mm, 2),
        "gross_irrigation_requirement_mm": gir_mm,
        "water_requirement_mm": gir_mm,
        "water_requirement_litres": water_litres,
        "water_requirement_m3": water_m3,
        "irrigation_efficiency_pct": irr_info["efficiency_pct"],
        "irrigation_recommended": irrigation_recommended,
        "urgency_level": urgency,
        "soil_source": soil_source,
        "usda_soil_texture": usda_soil_texture,
        "recommended_schedule": {
            "frequency_days": freq_days,
            "duration_hours": duration_hrs,
            "best_time": best_time,
            "emitter_discharge_lph": 4.0 if irrigation_method == "Drip" else None,
            "next_irrigation_date": next_date
        },
        "recommendations": recommendations,
        "timestamp": datetime.now().isoformat()
    }
