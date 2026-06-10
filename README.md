# 5D-data_IFC-integration

IfcOpenShell-based Python workflow for enriching IFC models with cost information exported from cost-estimation software. The script maps external cost records to IFC model elements through their `GlobalId` and writes the resulting information using IFC-native cost entities and relationships.

This repository is associated with the research paper *Interoperable 5D openBIM: cost data integration workflow and IFC-based analysis challenges*, which will be published soon in EG-ICE 2026 conference proceedings.

## Purpose

The repository supports an openBIM 5D workflow in which cost data are not stored as generic properties, but are embedded in the IFC model through a structured set of IFC entities. The workflow is intended to demonstrate how total costs, unit costs, and optional price-analysis components can be encoded directly in an IFC file while preserving their relationship with model elements.

The script creates and links the following main IFC entities:

- `IfcCostItem`, used to represent the cost item assigned to a model element;
- `IfcCostValue`, used to store total costs, unit costs, and optional price-analysis components;
- `IfcMeasureWithUnit`, used to associate cost values with monetary and measurement units;
- `IfcRelAssignsToControl`, used to connect each `IfcCostItem` to the corresponding IFC object.

## Workflow overview

The script performs the following operations:

1. loads an IFC model selected by the user;
2. loads a tabular cost-estimation file in `.csv`, `.xlsx`, or `.xls` format;
3. optionally loads a price-analysis `.csv` file;
4. reads the `GlobalId` of each model element from the cost-estimation data;
5. searches the corresponding object in the IFC model;
6. creates the required IFC cost structure using `IfcCostItem` and `IfcCostValue`;
7. links each cost item to the related IFC object through `IfcRelAssignsToControl`;
8. exports a new cost-enriched IFC file;
9. exports two traceability files listing the GUIDs that were found and not found in the IFC model.

## Repository structure

```text
5D-data_IFC-integration/
├── README.md
└── Script/
    └── 20260507_Integrate cost estimation in IFC model.py
```

## Requirements

The script requires Python and the following main packages:

```bash
pip install ifcopenshell pandas openpyxl
```

The script also uses `tkinter` to open file-selection dialogs. In most standard Python installations, `tkinter` is already included. If it is not available, it must be installed according to the operating system being used.

## Input files

### 1. IFC model

The input model must be an IFC file using the IFC4 schema or a later version. The script checks the schema before continuing.

### 2. Cost-estimation file

The main cost-estimation file can be provided as `.csv`, `.xlsx`, or `.xls`. For `.csv` files, the script currently uses `;` as delimiter.

The expected column names are:

| Column | Meaning |
| --- | --- |
| `GUID Oggetto BIM` | GlobalId of the IFC object to which the cost item is assigned |
| `Quantità` | Quantity associated with the cost item |
| `Des. U.M.` | Unit of measure |
| `Importo totale (Costo)` | Total cost assigned to the object for the selected cost item |
| `Prezzo totale (Costo)` | Unit cost used to calculate the total cost |
| `Articolo` | Cost item code or name |
| `Breve` | Cost item description |
| `Categoria` | Cost category |

### 3. Optional price-analysis file

The price-analysis file is optional and must be provided as `.csv`. It is used to describe the components that contribute to the unit cost.

The expected column names are:

| Column | Meaning |
| --- | --- |
| `Codice` | Parent cost item code |
| `Cod. Articolo` | Component item code |
| `Prezzo elementare` | Elementary price of the component |
| `Valore quantità` | Quantity of the component |
| `Des. Articolo` | Component description |
| `Unita' di misura` | Component unit of measure |
| `Categoria` | Component category, such as material, labor, or equipment |

## How to run the script

From the repository root, run:

```bash
python "Script/20260507_Integrate cost estimation in IFC model.py"
```

The script opens file-selection dialogs and asks the user to select:

1. the IFC model;
2. the main cost-estimation file;
3. optionally, the price-analysis file.

## Output files

The script exports the following files in the `IFC EXPORT COST FILES` folder (which will be created in the same directory of the IFC file):

| Output | Description |
| --- | --- |
| `<ifc_file_name>_TOTAL-UNIT-COSTS.ifc` | Cost-enriched IFC file containing total and unit costs (if no price analysis file was selected) |
| `<ifc_file_name>_PRICE-ANALYSIS.ifc` | Cost-enriched IFC file containing total costs, unit costs, and price-analysis components (if price analysis file was selected) |
| `guids_found_<ifc_file_name>.csv` | List of GUIDs successfully matched with IFC objects |
| `guids_not_found_<ifc_file_name>.csv` | List of GUIDs not found in the IFC model |

The exported IFC model stores the total cost at the element-assignment level and, when available, connects it to the corresponding unit cost and price-analysis components.

## Workflow diagrams and example result

### IFC-native cost-data structure

<img width="2942" height="1022" alt="Figure 1" src="https://github.com/user-attachments/assets/22328a14-d671-49c5-8ce5-10f5a3ad7b1d" />

### Script activity diagram

<img width="15605" height="5629" alt="img_2_300dpi" src="https://github.com/user-attachments/assets/72a8d0c0-18b0-4bef-8ca7-64d7450f99c9" />

### Example result in IFC STEP format

<img width="5239" height="2828" alt="img_4_300dpi" src="https://github.com/user-attachments/assets/9fb75628-5d3d-45b4-88bf-0c0efafe5424" />

## Notes and limitations

- The script is currently tailored to the column names exported from the tested cost-estimation workflow. If other estimating software or price-list formats are used, the column names and mapping rules must be adapted.
- Monetary values are written using `EUR` as the default currency.
- The script supports several common units of measure, including `m`, `m²`, `m³`, `kg`, `ton`, `hour`, `day`, `cad`, `%`, and other context-dependent units used in the tested workflow.
- Current IFC viewers may not fully display the relationships between `IfcCostItem`, `IfcCostValue`, and the related IFC objects. For this reason, a companion web-based BIM viewer has been developed to read and visualize the cost structure generated by this workflow: https://github.com/limlab-unipd/bim-app-viewer. Direct inspection of the IFC STEP file may still be useful to verify the complete cost structure.
- The workflow focuses on element-related cost assignments. More complex cost structures, such as overheads, temporary works, assemblies, or contractual adjustments, may require additional modelling strategies.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Authors

Developed by **Ygor Fasanella**, PhD candidate at the University of Padua, Department of Civil, Environmental and Architectural Engineering.

Research supervision and scientific contribution: **Paolo Borin**.
