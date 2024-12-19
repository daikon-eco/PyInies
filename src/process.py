import pandas as pd
from typing import List
import numpy as np

from .models import Epd


def process_all_epds(all_epds: List[Epd]) -> pd.DataFrame:
    df = pd.DataFrame(epd.model_dump() for epd in all_epds)
    df["responsibleOrganism"] = df["responsibleOrganism"].apply(lambda x: x["name"])
    df["norme"] = df["indicatorSet"].apply(lambda x: x["name"])

    normalized_indicator_set = pd.DataFrame(
        pd.json_normalize(df.indicatorSet)["indicatorQuantities"]
    )
    normalized_indicator_set["id"] = df["id"]
    exploded = normalized_indicator_set.explode("indicatorQuantities").reset_index(
        drop=True
    )
    normalized_quantities = pd.json_normalize(exploded["indicatorQuantities"])
    normalized_quantities["id"] = exploded["id"]
    normalized_quantities = normalized_quantities[
        normalized_quantities.indicatorId.isin([2, 19, 45, 19, 57])
    ]
    normalized_quantities.drop_duplicates(subset=["id", "phaseName"], inplace=True)

    pivoted_quantities = normalized_quantities.pivot(
        index="id", columns="phaseName", values="quantity"
    ).reset_index()

    df = df.merge(pivoted_quantities, on="id", how="left")
    df.fuConstituantProducts = df.fuConstituantProducts.apply(
        lambda constituants: " ; ".join(
            f"{constituant["name"]} {constituant["quantity"]} {constituant["unit"]}"
            for constituant in constituants
        )
    )
    df.drop(columns="indicatorSet", inplace=True)
    df.productionRegionFr = df.productionRegionFr.apply(
        lambda regions: None if regions == [] else " ; ".join(regions)
    )
    df.commercialReferences = (
        df.commercialReferences.str.replace("\r\n", " ; ")
        .str.replace("\r", " ; ")
        .str.replace("\n", " ; ")
    )

    cols = ("Étape de production", "Production")
    df[cols[0]] = df.apply(
        lambda row: row[cols[0]] if pd.notna(row[cols[0]]) else row[cols[1]], axis=1
    )

    cols = ("A4-Transport", "Transport")
    df[cols[0]] = df.apply(
        lambda row: row[cols[0]] if pd.notna(row[cols[0]]) else row[cols[1]], axis=1
    )

    cols = ("Étape d’utilisation", "Vie en oeuvre")
    df[cols[0]] = df.apply(
        lambda row: row[cols[0]] if pd.notna(row[cols[0]]) else row[cols[1]], axis=1
    )

    cols = ("Étape de fin de vie", "Fin de vie")
    df[cols[0]] = df.apply(
        lambda row: row[cols[0]] if pd.notna(row[cols[0]]) else row[cols[1]], axis=1
    )

    df["A"] = np.maximum(
        df["Étape de production"].fillna(0)
        + df["Étape du processus de construction"].fillna(0),
        df["Étape de production"].fillna(0)
        + df["A4-Transport"].fillna(0)
        + df["A5-Processus de construction – installation"].fillna(0),
    )

    df.issueDate = df.issueDate.apply(
        lambda x: x.strftime("%Y/%m/%d") if pd.notna(x) else x
    )

    return df


def modify_columns_names(df: pd.DataFrame) -> pd.DataFrame:
    columns_mapping = {
        "name": "Name_FDES",
        "serialIdentifier": "ID_FDES",
        "id": "Unique_ID_FDES_version",
        "version": "Version",
        "issueDate": "Issue_Date",
        "declarationType": "Declaration_Type",
        "declarationTypeName": "Declaration_Type_Name",
        "norme": "Norme",
        "responsibleOrganism": "Organisme_Name",
        "dvt": "DVT",
        "ufQuantity": "UF_Quantity",
        "ufUnit": "UF_Unit",
        "ufDescription": "UF_Description",
        "commercialReferences": "Commercial_References",
        "Total cycle de vie": "Total",
        "A": "A",
        "Étape d’utilisation": "B",
        "Étape de fin de vie": "C",
        "D-Bénéfices et charges au-delà des frontières du système": "D",
        "A1-Approvisionnement en matières premières": "A1",
        "A2-Transport": "A2",
        "A3-Fabrication": "A3",
        "Étape de production": "A1-A3",
        "A4-Transport": "A4",
        "A5-Processus de construction – installation": "A5",
        "Étape du processus de construction": "A4-A5",
        "B1-Utilisation": "B1",
        "B2-Maintenance": "B2",
        "B3-Réparation": "B3",
        "B4-Remplacement": "B4",
        "B5-Réhabilitation": "B5",
        "B6-Utilisation de l’énergie durant l’étape d’utilisation": "B6",
        "B7-Utilisation de l’eau durant l’étape d’utilisation": "B7",
        "C1-Déconstruction / démolition": "C1",
        "C2-Transport": "C2",
        "C3-Traitement des déchets": "C3",
        "C4-Élimination": "C4",
        "carbonBiogenicStorage": "CarbonBiogenicStorage",
        "packagingCarbonBiogenicStorage": "Packaging_Carbone_Biogenic_Storage",
        "distanceTransportA4Km": "Distance_Transport_A4_Km",
        "productionPlace": "Production_Place",
        "productionRegionFr": "Production_Region_FR",
        "fuConstituantProducts": "Constituant_Products",
    }

    return df.rename(columns=columns_mapping)[columns_mapping.values()]
