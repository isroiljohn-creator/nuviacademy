import os
import csv
import psycopg2
from psycopg2.extras import execute_values
import sys
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def map_headers(reader_fieldnames, target_table):
    """
    Maps CSV headers to database columns.
    USDA FDC files usually have specific headers.
    """
    mappings = {
        'usda.food': {
            'fdc_id': 'fdc_id',
            'description': 'description',
            'data_type': 'data_type',
            'food_category_id': 'food_category_id',
            'publication_date': 'publication_date'
        },
        'usda.nutrient': {
            'id': 'id',
            'name': 'name',
            'unit_name': 'unit_name',
            'nutrient_nbr': 'nutrient_nbr'
        },
        'usda.food_nutrient': {
            'fdc_id': 'fdc_id',
            'nutrient_id': 'nutrient_id',
            'amount': 'amount'
        }
    }
    
    target_mapping = mappings.get(target_table, {})
    actual_mapping = {}
    
    print(f"  Headers found: {reader_fieldnames}")
    
    required_cols = list(target_mapping.keys())
    
    for target_col in required_cols:
        matched = False
        csv_col_candidate = target_mapping[target_col]
        
        # Try exact match
        if csv_col_candidate in reader_fieldnames:
            actual_mapping[csv_col_candidate] = target_col
            matched = True
        else:
            # Try case-insensitive or common variations
            for field in reader_fieldnames:
                if field.lower() == csv_col_candidate.lower():
                    actual_mapping[field] = target_col
                    matched = True
                    break
        
        if not matched and target_col in ['fdc_id', 'description', 'id', 'name', 'nutrient_id', 'amount']:
            print(f"❌ ERROR: Required column '{target_col}' not found in CSV for {target_table}!")
            return None
                    
    return actual_mapping

def import_csv(file_path, table_name, chunk_size=10000):
    if not os.path.exists(file_path):
        print(f"Skipping {file_path}: File not found.")
        return

    print(f"\nStarting import for {file_path} into {table_name}...")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        with open(file_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            mapping = map_headers(reader.fieldnames, table_name)
            
            if mapping is None:
                print(f"❌ STOPPING: Header mapping failed for {table_name}. Check CSV format.")
                sys.exit(1)

            columns = list(mapping.values())
            csv_cols = list(mapping.keys())
            
            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)}) 
                VALUES %s 
                ON CONFLICT (fdc_id{', nutrient_id' if 'food_nutrient' in table_name else ''}{'id' if 'nutrient' in table_name and 'food_nutrient' not in table_name else ''}) DO NOTHING
            """
            # Adjusting conflict target for usda.nutrient which has PK 'id'
            if table_name == 'usda.nutrient':
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s ON CONFLICT (id) DO NOTHING"
            elif table_name == 'usda.food':
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s ON CONFLICT (fdc_id) DO NOTHING"
            elif table_name == 'usda.food_nutrient':
                query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES %s ON CONFLICT (fdc_id, nutrient_id) DO NOTHING"

            batch = []
            count = 0
            
            for row in reader:
                val = tuple(row.get(col) if row.get(col) else None for col in csv_cols)
                batch.append(val)
                count += 1
                
                if len(batch) >= chunk_size:
                    execute_values(cur, query, batch)
                    conn.commit()
                    batch = []
                    print(f"  Processed {count} rows...")
            
            if batch:
                execute_values(cur, query, batch)
                conn.commit()
                print(f"  Processed {count} rows (final batch).")
                
        print(f"✅ Successfully imported {count} rows into {table_name}.")
        
    except sys.exit as e:
        raise e
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/usda"
    
    # 1. Nutrients (dependencies first)
    import_csv(os.path.join(data_dir, "nutrient.csv"), "usda.nutrient")
    
    # 2. Food
    import_csv(os.path.join(data_dir, "food.csv"), "usda.food")
    
    # 3. Food Nutrient (junction)
    import_csv(os.path.join(data_dir, "food_nutrient.csv"), "usda.food_nutrient")
