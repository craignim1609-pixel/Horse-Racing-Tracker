import pandas as pd

def export_to_excel(data: list[dict], filename: str) -> str:
    """
    Exports a list of dictionaries to an Excel file.
    Ensures safe handling of empty data and consistent column ordering.
    """
    if not data:
        # Create an empty sheet with no rows but valid file
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(data)

    df.to_excel(filename, index=False)
    return filename
