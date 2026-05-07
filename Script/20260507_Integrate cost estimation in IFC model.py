import ifcopenshell
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import time
import os
import math

#region COLUMNS TO IMPORT
# Define the column names to import from the Excel/CSV file for TOTAL COST AND UNIT COST
column_guid="GUID Oggetto BIM"
column_quantity="Quantità"
column_unitMeasure="Des. U.M."
column_totalCost="Importo totale (Costo)"
column_unitCost="Prezzo totale (Costo)"
column_costItemName="Articolo"
column_costItemDescription="Breve"
column_categoria="Categoria"
# Define the column names to import from the Excel/CSV file for PRICE LIST
column_parent_code = "Codice"
column_child_code = "Cod. Articolo"
column_pa_prezzoElementare = "Prezzo elementare"
column_pa_valoreQuantita = "Valore quantità"
column_pa_descrizioneArticolo = "Des. Articolo"
column_pa_unitaMisura = "Unita' di misura"
column_pa_categoria = "Categoria"

csv_delimiter = ";"
#endregion

#region SELECT FILES - IFC, EXCEL/CSV, PRICE LIST
def ask_file(title, filetypes):
    return filedialog.askopenfilename(title=title, filetypes=filetypes)

root = tk.Tk()
root.withdraw()

# Select IFC file
ifc_path = ask_file("Select an IFC file", [("IFC files", "*.ifc")])
if not ifc_path:
    raise FileNotFoundError("No IFC file selected.")
ifc_dir = os.path.dirname(os.path.abspath(ifc_path))

# Select Excel/CSV file with total and unit costs
data_path = ask_file("Select Excel or CSV file (total and unit costs)", [("", "*.xlsx *.xls *.csv")])
if not data_path:
    raise FileNotFoundError("No data file selected.")

# Ask whether to load the analysis prices CSV
load_analysis = messagebox.askyesno(
    title="Pricy Analysis",
    message="Would you like to load CSV file with price analysis details?"
)
# Select analysis prices CSV only if requested
analysis_path = ""
if load_analysis:
    analysis_path = ask_file("Select CSV file (price analysis)", [("CSV files", "*.csv")])
analysis_loaded = bool(analysis_path)
root.destroy()
ifc_name = os.path.splitext(os.path.basename(ifc_path))[0]
#endregion

#region READ IFC AND EXCEL/CSV FILES
# Load IFC
start_ifc = time.time()
ifc_file = ifcopenshell.open(ifc_path)
end_ifc = time.time()
print(f"Time to load IFC file: {end_ifc - start_ifc:.2f} seconds")
if not ifc_file.schema.upper().startswith("IFC4"):
    raise ValueError(f"Unsupported IFC schema: {ifc_file.schema}. Please use an IFC4 or later file.")

columns_to_import = [column_guid, column_quantity, column_unitMeasure, column_unitCost, column_totalCost, column_costItemName, column_costItemDescription, column_categoria]
start_data = time.time()
file_ext = os.path.splitext(data_path)[1].lower()
try:
    if file_ext == ".xlsx":
        data = pd.read_excel(data_path, usecols=columns_to_import)
    elif file_ext == ".csv":
        try:
            data = pd.read_csv(data_path, usecols=columns_to_import, encoding="utf-8", sep=csv_delimiter, engine="python")
        except UnicodeDecodeError:
            data = pd.read_csv(data_path, usecols=columns_to_import, encoding="latin1", sep=csv_delimiter, engine="python")  # o "ISO-8859-1"
        # Ora filtra solo le colonne desiderate
        data = data[[col for col in columns_to_import if col in data.columns]]
    else:
        raise ValueError("Unsupported file format. Please select a .xlsx or .csv file.")
except ValueError as e:
    raise ValueError(f"Error reading data file: {e}")

end_data = time.time()
print(f"Time to load data file: {end_data - start_data:.2f} seconds")
print("Preview of selected columns:")
print(data.head())

# Read analysis prices CSV
pa_columns_to_import = [column_parent_code, column_child_code, column_pa_prezzoElementare, column_pa_valoreQuantita, column_pa_descrizioneArticolo, column_pa_unitaMisura, column_pa_categoria]
if analysis_loaded:
    start_data = time.time()
    file_ext = os.path.splitext(analysis_path)[1].lower()
    try:
        if file_ext == ".xlsx":
            analysis_df = pd.read_excel(analysis_path, usecols=pa_columns_to_import)
        elif file_ext == ".csv":
            try:
                analysis_df = pd.read_csv(analysis_path, usecols=pa_columns_to_import, encoding="utf-8", sep=csv_delimiter, engine="python")
            except UnicodeDecodeError:
                analysis_df = pd.read_csv(analysis_path, usecols=pa_columns_to_import, encoding="latin1", sep=csv_delimiter, engine="python")  # o "ISO-8859-1"
            # Ora filtra solo le colonne desiderate
            analysis_df = analysis_df[[col for col in pa_columns_to_import if col in analysis_df.columns]]
        else:
            raise ValueError("Unsupported file format. Please select a .xlsx or .csv file.")
    except ValueError as e:
        raise ValueError(f"Error reading data file: {e}")

    end_data = time.time()
    print(f"Time to load price analysis data file: {end_data - start_data:.2f} seconds")
    print("Preview of selected columns:")
    print(analysis_df.head())
else:
    analysis_df = pd.DataFrame(columns=pa_columns_to_import)
    print("No analysis prices file selected. Continuing without price analysis.")
#endregion

#region ADD BASIC UNITS TO IFC FILE
# how to add a new unit:
# 1. create a new entity such as below here --> these are the generic unit of measure
# 2. create the new corresponding unitbasis for unit price --> here is created the instance of IfcMeasureWithUnit with quantity = 1
# 3. add new if condition to choose the corret enetity if total or unit cost --> here is created the instance of IfcMeasureWithUnit with the object quantity
# keeping separeted unit and total entities ensure to not create a new entity for unit prices each iteration, but getting the already created ones
dimensionalExponents_0000000 = ifc_file.create_entity(
    "IfcDimensionalExponents",
    LengthExponent=0,
    MassExponent=0,
    TimeExponent=0,
    ElectricCurrentExponent=0,
    ThermodynamicTemperatureExponent=0,
    AmountOfSubstanceExponent=0,
    LuminousIntensityExponent=0,
)
dimensionalExponents_Time = ifc_file.create_entity(
    "IfcDimensionalExponents",
    LengthExponent=0,
    MassExponent=0,
    TimeExponent=1,
    ElectricCurrentExponent=0,
    ThermodynamicTemperatureExponent=0,
    AmountOfSubstanceExponent=0,
    LuminousIntensityExponent=0,
)
dimensionalExponents_Mass = ifc_file.create_entity(
    "IfcDimensionalExponents",
    LengthExponent=0,
    MassExponent=1,
    TimeExponent=0,
    ElectricCurrentExponent=0,
    ThermodynamicTemperatureExponent=0,
    AmountOfSubstanceExponent=0,
    LuminousIntensityExponent=0,
)

monetaryUnit_EUR = ifc_file.create_entity(
    "IfcMonetaryUnit",
    "EUR"
)
monetaryUnit_USD = ifc_file.create_entity(
    "IfcMonetaryUnit",
    "USD"
)
areaUnit_squareMetre = ifc_file.create_entity(
    "IfcSIUnit",
    UnitType="AREAUNIT",
    Name="SQUARE_METRE",
)
volumeUnit_cubicMetre = ifc_file.create_entity(
    "IfcSIUnit",
    UnitType="VOLUMEUNIT",
    Name="CUBIC_METRE",
)
lengthUnit_Metre = ifc_file.create_entity(
    "IfcSIUnit",
    UnitType="LENGTHUNIT",
    Name="METRE",
)
massUnit_Gram = ifc_file.create_entity(
    "IfcSIUnit",
    UnitType="MASSUNIT",
    Name="GRAM",
)
timeUnit_Second = ifc_file.create_entity(
    "IfcSIUnit",
    UnitType="TIMEUNIT",
    Name="SECOND",
)
contextDependentUnit_cad = ifc_file.create_entity(
    "IfcContextDependentUnit",
    Dimensions=dimensionalExponents_0000000,
    UnitType="USERDEFINED",
    Name="cad"
)
contextDependentUnit_m2cm = ifc_file.create_entity(
    "IfcContextDependentUnit",
    Dimensions=dimensionalExponents_0000000,
    UnitType="USERDEFINED",
    Name="m²/cm"
)
contextDependentUnit_m2mm = ifc_file.create_entity(
    "IfcContextDependentUnit",
    Dimensions=dimensionalExponents_0000000,
    UnitType="USERDEFINED",
    Name="m²/mm"
)
contextDependentUnit_perc = ifc_file.create_entity(
    "IfcContextDependentUnit",
    Dimensions=dimensionalExponents_0000000,
    UnitType="USERDEFINED",
    Name="%"
)
contextDependentUnit_acorpo = ifc_file.create_entity(
    "IfcContextDependentUnit",
    Dimensions=dimensionalExponents_0000000,
    UnitType="USERDEFINED",
    Name="a corpo"
)
contextDependentUnit_scatola = ifc_file.create_entity(
    "IfcContextDependentUnit",
    Dimensions=dimensionalExponents_0000000,
    UnitType="USERDEFINED",
    Name="scatola"
)
conversionBasedUnit_hour = ifc_file.create_entity(
    "IfcConversionBasedUnit",
    Dimensions=dimensionalExponents_Time,
    UnitType="TIMEUNIT",
    Name="hour",
    ConversionFactor=ifc_file.create_entity(
        "IfcMeasureWithUnit",
        ValueComponent=ifc_file.create_entity(
            "IfcTimeMeasure",
            3600
        ),
        UnitComponent=timeUnit_Second,
    ),
)
conversionBasedUnit_kg = ifc_file.create_entity(
    "IfcConversionBasedUnit",
    Dimensions=dimensionalExponents_Mass,
    UnitType="MASSUNIT",
    Name="kg",
    ConversionFactor=ifc_file.create_entity(
        "IfcMeasureWithUnit",
        ValueComponent=ifc_file.create_entity(
            "IfcMassMeasure",
            1000
        ),
        UnitComponent=massUnit_Gram,
    ),
)
conversionBasedUnit_ton = ifc_file.create_entity(
    "IfcConversionBasedUnit",
    Dimensions=dimensionalExponents_Mass,
    UnitType="MASSUNIT",
    Name="ton",
    ConversionFactor=ifc_file.create_entity(
        "IfcMeasureWithUnit",
        ValueComponent=ifc_file.create_entity(
            "IfcMassMeasure",
            1000000
        ),
        UnitComponent=massUnit_Gram,
    ),
)
conversionBasedUnit_quintale = ifc_file.create_entity(
    "IfcConversionBasedUnit",
    Dimensions=dimensionalExponents_Mass,
    UnitType="MASSUNIT",
    Name="100kg",
    ConversionFactor=ifc_file.create_entity(
        "IfcMeasureWithUnit",
        ValueComponent=ifc_file.create_entity(
            "IfcMassMeasure",
            100000
        ),
        UnitComponent=massUnit_Gram,
    ),
)
conversionBasedUnit_day = ifc_file.create_entity(
    "IfcConversionBasedUnit",
    Dimensions=dimensionalExponents_Time,
    UnitType="TIMEUNIT",
    Name="day",
    ConversionFactor=ifc_file.create_entity(
        "IfcMeasureWithUnit",
        ValueComponent=ifc_file.create_entity(
            "IfcTimeMeasure",
            86400
        ),
        UnitComponent=timeUnit_Second,
    ),
)
#endregion

#region UNIT WITH MEASURE FOR UNIT COST VALUES
unitbasis_cad = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcReal", 1),
    UnitComponent=contextDependentUnit_cad
)
unitbasis_metre = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcLengthMeasure", 1),
    UnitComponent=lengthUnit_Metre
)
unitbasis_squaremetre = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcAreaMeasure", 1),
    UnitComponent=areaUnit_squareMetre
)
unitbasis_cubicmetre = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcVolumeMeasure", 1),
    UnitComponent=volumeUnit_cubicMetre
)
unitbasis_cubicmetre = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcVolumeMeasure", 1),
    UnitComponent=volumeUnit_cubicMetre
)
unitbasis_kilogram = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcMassMeasure", 1),
    UnitComponent=conversionBasedUnit_kg
)
unitbasis_ton = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcMassMeasure", 1),
    UnitComponent=conversionBasedUnit_ton
)
unitbasis_quintale = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcMassMeasure", 1),
    UnitComponent=conversionBasedUnit_quintale
)
unitbasis_day = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcTimeMeasure", 1),
    UnitComponent=conversionBasedUnit_day
)
unitbasis_hour = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcTimeMeasure", 1),
    UnitComponent=conversionBasedUnit_hour
)
unitbasis_m2cm = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcReal", 1),
    UnitComponent=contextDependentUnit_m2cm
)
unitbasis_m2mm = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcReal", 1),
    UnitComponent=contextDependentUnit_m2mm
)
unitbasis_perc = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcReal", 1),
    UnitComponent=contextDependentUnit_perc
)
unitbasis_acorpo = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcReal", 1),
    UnitComponent=contextDependentUnit_acorpo
)
unitbasis_scatola = ifc_file.create_entity(
    "IfcMeasureWithUnit",
    ValueComponent=ifc_file.create_entity("IfcReal", 1),
    UnitComponent=contextDependentUnit_scatola
)
#endregion

#region FUNCTION TO CREATE IFCMEASUREWITHUNIT (choosing between total or unitary)
def create_unit_basis(quantita,unita_misura,usage="unit"):
    if (quantita is None or quantita == 'nan' or quantita == '' or pd.isna(quantita)):
        quantita = 0
    if (unita_misura == "Cadauno" or unita_misura == "cad" or unita_misura == "CAD" or unita_misura == "conf." or unita_misura == "pz"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcReal", quantita),
                UnitComponent=contextDependentUnit_cad
            )
        elif (usage == "unit"):
            return unitbasis_cad
    elif (unita_misura == "m" or unita_misura == "M" or unita_misura == "ml"): #ml=metro lineare
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcLengthMeasure", quantita),
                UnitComponent=lengthUnit_Metre
            )
        elif (usage == "unit"):
            return unitbasis_metre
    elif (unita_misura == "m²" or unita_misura == "mq" or unita_misura == "M2"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcAreaMeasure", quantita),
                UnitComponent=areaUnit_squareMetre
            )
        elif (usage == "unit"):
            return unitbasis_squaremetre
    elif (unita_misura == "m³" or unita_misura == "mc" or unita_misura == "M3"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcVolumeMeasure", quantita),
                UnitComponent=volumeUnit_cubicMetre
            )
        elif (usage == "unit"):
            return unitbasis_cubicmetre
    elif (unita_misura == "kg" or unita_misura == "KG"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcMassMeasure", quantita),
                UnitComponent=conversionBasedUnit_kg
            )
        elif (usage == "unit"):
            return unitbasis_kilogram
    elif (unita_misura == "ton" or unita_misura == "T"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcMassMeasure", quantita),
                UnitComponent=conversionBasedUnit_ton
            )
        elif (usage == "unit"):
            return unitbasis_ton
    elif (unita_misura == "100kg" or unita_misura == "quintale"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcMassMeasure", quantita),
                UnitComponent=conversionBasedUnit_quintale
            )
        elif (usage == "unit"):
            return unitbasis_quintale
    elif (unita_misura == "hour" or unita_misura == "h" or unita_misura == "H" or unita_misura == "ora"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcTimeMeasure", quantita),
                UnitComponent=conversionBasedUnit_hour
            )
        elif (usage == "unit"):
            return unitbasis_hour
    elif (unita_misura == "day" or unita_misura == "giorno"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcTimeMeasure", quantita),
                UnitComponent=conversionBasedUnit_day
            )
        elif (usage == "unit"):
            return unitbasis_day
    elif (unita_misura == "m²/cm"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcReal", quantita),
                UnitComponent=contextDependentUnit_m2cm
            )
        elif (usage == "unit"):
            return unitbasis_m2cm
    elif (unita_misura == "m²/mm"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcReal", quantita),
                UnitComponent=contextDependentUnit_m2mm
            )
        elif (usage == "unit"):
            return unitbasis_m2mm
    elif (unita_misura == "%"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcReal", quantita),
                UnitComponent=contextDependentUnit_perc
            )
        elif (usage == "unit"):
            return unitbasis_perc
    elif (unita_misura == "a corpo" or unita_misura == "AC"):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcReal", quantita),
                UnitComponent=contextDependentUnit_acorpo
            )
        elif (usage == "unit"):
            return unitbasis_acorpo
    elif (unita_misura == "scat." or unita_misura == "scatola" or unita_misura == "scat" or unita_misura == "conf" ):
        if (usage=="total"):
            unitbasis = ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcReal", quantita),
                UnitComponent=contextDependentUnit_scatola
            )
        elif (usage == "unit"):
            return unitbasis_scatola
    return unitbasis
#endregion

#region FUNCTION TO CREATE OR GET UNIT COST IF ALREADY CREATED
# Cache to avoid duplication of unitary cost values
unit_costs_cache = {}  # key: (prezzo_unitario, articolo, breve, category)
def get_or_create_unit_cost(prezzo_unitario, articolo, breve, unita_misura, components=[], category="Unit cost"): #here the cost value is created or get
    unit_basis = create_unit_basis(quantita=1,unita_misura=unita_misura, usage="unit") #here is get the entity for the UnitBasis attribute
    key = (prezzo_unitario, articolo, breve, category)
    if key in unit_costs_cache:
        unit_cost = unit_costs_cache[key]
    else:
        if (components == []):
            unit_cost = ifc_file.create_entity(
                "IfcCostValue",
                Name=articolo,
                Description=breve,
                AppliedValue=ifc_file.create_entity(
                    "IfcMeasureWithUnit",
                    ValueComponent=ifc_file.create_entity("IfcReal", prezzo_unitario),
                    UnitComponent=monetaryUnit_EUR
                ),
                UnitBasis=unit_basis,
                Category=category,
            )
        else:
            unit_cost = ifc_file.create_entity(
                "IfcCostValue",
                Name=articolo,
                Description=breve,
                AppliedValue=ifc_file.create_entity(
                    "IfcMeasureWithUnit",
                    ValueComponent=ifc_file.create_entity("IfcReal", prezzo_unitario),
                    UnitComponent=monetaryUnit_EUR
                ),
                UnitBasis=unit_basis,
                Category=category,
                Components=components,
            )
        unit_costs_cache[key] = unit_cost
    return unit_cost

price_analysis_cache = {}  # key: (prezzo_unitario, articolo, breve, category)
def get_or_create_price_analysis(prezzo_unitario, articolo, breve, unita_misura, quantita, category="Price analysis"): #here the cost value is created or get
    pa_unit_basis = create_unit_basis(quantita=quantita,unita_misura=unita_misura, usage="total") #here is get the entity for the UnitBasis attribute
    key = (prezzo_unitario, articolo, breve, quantita, category)
    if key in price_analysis_cache:
        unit_cost = price_analysis_cache[key]
    else:
        unit_cost = ifc_file.create_entity(
            "IfcCostValue",
            Name=articolo,
            Description=breve,
            AppliedValue=ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity("IfcReal", prezzo_unitario),
                UnitComponent=monetaryUnit_EUR
            ),
            UnitBasis=pa_unit_basis,
            Category=category,
        )
        price_analysis_cache[key] = unit_cost
    return unit_cost
#endregion

#region CREATE AND ADD COST ITEMS TO IFC MODEL
guid_notfound = []
guid_found = []

for index, row in data.iterrows(): #loop over each row of excel file
    #read columns of imported excel or csv file
    guid = row[column_guid]
    importo_totale = row[column_totalCost]
    try:
        importo_totale_finito = pd.notna(importo_totale) and math.isfinite(float(importo_totale))
    except (TypeError, ValueError):
        importo_totale_finito = False

    if importo_totale_finito is False:
        # print(importo_totale)
        # print(row)
        importo_totale = 0  # Set a default value or skip this row if total cost is not valid

    articolo = row[column_costItemName] # Name
    breve = row[column_costItemDescription] # Description
    prezzo_unitario = row[column_unitCost]
    quantita = row[column_quantity]
    unita_misura = row[column_unitMeasure]
    categoria = row[column_categoria] if column_categoria in row else "Uncategorized"

    try:
        target_element = ifc_file.by_guid(guid)
        if not target_element: #if element is not found skip the entire iteration and go to the next one
            guid_notfound.append(guid)
            continue
    except Exception as e:
        #print(f"Error searching for GUID {guid}: {e}")
        guid_notfound.append(guid)
        continue
    guid_found.append(guid) #only to keep count of iterations
    
    pa_children = []
    if analysis_loaded:
        # --- PRICE ANALYSIS ---
        analysis_rows = analysis_df[analysis_df[column_parent_code] == articolo]
        #print("analysis_rows:", analysis_rows)

        if analysis_rows.empty:
            # the same article is recreated and set as component, because if it has no price analysis it is the price analysis itself
            pa_unit_cost = get_or_create_unit_cost(prezzo_unitario, articolo, breve, unita_misura, category=categoria)
            pa_children.append(pa_unit_cost)
        else:
            #print(f"\nArticolo {articolo}:")
            #children_codes = analysis_rows[column_child_code].dropna().tolist()
            for pa_index, pa_row in analysis_rows.iterrows():
                pa_prezzo_elementare = pa_row[column_pa_prezzoElementare]
                pa_quantita = pa_row[column_pa_valoreQuantita]
                if (pd.isna(pa_prezzo_elementare) or pa_prezzo_elementare == 0 or pa_prezzo_elementare is None or pd.isna(pa_quantita) or pa_quantita == 0 or pa_quantita is None):
                    continue  # Skip this child if unit price is zero or None
                pa_prezzo_totale = pa_prezzo_elementare * pa_quantita
                pa_articolo = pa_row[column_child_code]
                pa_descrizione = pa_row[column_pa_descrizioneArticolo]
                pa_unita_misura = pa_row[column_pa_unitaMisura]
                pa_categoria = pa_row[column_pa_categoria] if column_pa_categoria in pa_row else "Uncategorized"
                
                pa_unit_cost = get_or_create_price_analysis(pa_prezzo_totale, pa_articolo, pa_descrizione, pa_unita_misura, pa_quantita, category=pa_categoria)
                #pa_unit_basis = create_unit_basis(pa_quantita, pa_unita_misura, usage="unit")
                pa_children.append(pa_unit_cost)
            #print(children)

    #create IfcCostValue instance for unit cost
    unit_cost = get_or_create_unit_cost(prezzo_unitario, articolo, breve, unita_misura, pa_children) #this is the unit cost value, get the already created entity if present otherwise creates a new one
    unit_basis = create_unit_basis(quantita, unita_misura, usage="total") #this is the total cost value, always new entity

    if unit_cost:
        #create IfcCostValue instance for total cost
        cost_value = ifc_file.create_entity(
            "IfcCostValue",
            AppliedValue=ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity(
                    "IfcReal",
                    importo_totale),
                UnitComponent=monetaryUnit_EUR
                ),
            UnitBasis=unit_basis,
            Category="Total cost",
            Components=[unit_cost],
        )
    else:
        #create IfcCostValue instance for total cost
        cost_value = ifc_file.create_entity(
            "IfcCostValue",
            AppliedValue=ifc_file.create_entity(
                "IfcMeasureWithUnit",
                ValueComponent=ifc_file.create_entity(
                    "IfcReal",
                    importo_totale),
                UnitComponent=monetaryUnit_EUR
                ),
            UnitBasis=unit_basis,
            Category="Total cost",
        )

    
    # Check if target element has owner history attribute, otherwise select the default one from IfcProject
    if hasattr(target_element, "OwnerHistory") and target_element.OwnerHistory:
        owner_history = target_element.OwnerHistory
    else:
        project = ifc_file.by_type("IfcProject")[0]
        owner_history = project.OwnerHistory
        
    #create IfcCostItem instance
    cost_item = ifc_file.create_entity(
        "IfcCostItem",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name=f"{articolo}",
        Description=f"{breve}",
        ObjectType= "Cost assignment",
        PredefinedType="USERDEFINED",
        CostValues=[cost_value]
        #CostQuantities not assigned because cost item refer to total cost
    )

    # create the IfcRelAssignsToControl instance to connect cost item to target element
    rel = ifc_file.create_entity(
        "IfcRelAssignsToControl",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=owner_history,
        Name="Cost-Object relation",
        Description=f"Articolo {articolo} to object {guid}",
        RelatedObjects=[target_element],
        RelatingControl=cost_item
    )
#endregion

#region EXPORT
# all the file wil be exported in the folder of the script
print("Found guids: ",len(guid_found))
print("Not found guids: ",len(guid_notfound))

# export new ifc file with costs added in the same directory of ifc file
if (analysis_loaded):
    output_filename = f"{ifc_name}_PRICE-ANALYSIS.ifc"
else:
    output_filename = f"{ifc_name}_TOTAL-UNIT-COSTS.ifc"
#output_filename = "PRICE ANALYSIS TEST.ifc"
output_path = os.path.join(ifc_dir, 'IFC EXPORT COST FILES', output_filename)
ifc_export_start=time.time()
ifc_file.write(output_path)
ifc_export_end=time.time()
print(f"Time to export IFC file: {ifc_export_end - ifc_export_start:.2f} seconds")

# export guids found and not found in the same directory of ifc file
pd.DataFrame({f"Found GUIDs ({len(guid_found)})": guid_found}).to_csv(os.path.join(ifc_dir, 'IFC EXPORT COST FILES', f"guids_found_{ifc_name}.csv"), index=False)
pd.DataFrame({f"Not Found GUIDs ({len(guid_notfound)})": guid_notfound}).to_csv(os.path.join(ifc_dir, 'IFC EXPORT COST FILES', f"guids_not_found_{ifc_name}.csv"), index=False)
#endregion
