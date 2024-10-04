import sqlite3


def create_database():
    conn = sqlite3.connect('mouse_study.db')
    cursor = conn.cursor()

    # Create Cohort table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Cohort (
        Cohort_id INTEGER PRIMARY KEY,
        CohortName TEXT UNIQUE,
        DOB DATE
    )
    ''')

    # Create MouseData table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS MouseData (
        EarTag INTEGER PRIMARY KEY,
        Sex TEXT,
        DOB DATE,
        DOD DATE,
        DeathDetails TEXT,
        DeathNotes TEXT,
        Necropsy BOOLEAN,
        Stagger INTEGER,
        Group_Number INTEGER,
        Cohort_id INTEGER,
        FOREIGN KEY (Group_Number) REFERENCES "Group"(Number),
        FOREIGN KEY (Cohort_id) REFERENCES Cohort(Cohort_id)
    )
    ''')

    # Create Group table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Group" (
        Number INTEGER PRIMARY KEY,
        Cohort_id INTEGER,
        Rapamycin TEXT CHECK(Rapamycin IN ('naive', 'mock', 'active')),
        HSCs TEXT CHECK(HSCs IN ('naive', 'mock', 'active')),
        Senolytic TEXT CHECK(Senolytic IN ('naive', 'mock', 'active')),
        Mobilization TEXT,
        AAV9 TEXT,
        FOREIGN KEY (Cohort_id) REFERENCES Cohort(Cohort_id)
    )
    ''')

    # Create Weights table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Weights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        EarTag INTEGER,
        Date DATE,
        Baseline BOOLEAN,
        Weight REAL,
        FOREIGN KEY (EarTag) REFERENCES MouseData(EarTag)
    )
    ''')

    # Create Rotarod table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Rotarod (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        EarTag INTEGER,
        Baseline BOOLEAN,
        Cull_date DATE,
        Date DATE,
        Time TIME,
        Speed REAL,
        FOREIGN KEY (EarTag) REFERENCES MouseData(EarTag)
    )
    ''')

    # Create GripStrength table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS GripStrength (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        EarTag INTEGER,
        Date DATE,
        ValueIndex INTEGER,
        Value REAL,
        FOREIGN KEY (EarTag) REFERENCES MouseData(EarTag)
    )
    ''')

    # Create indices
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mousedata_eartag ON MouseData(EarTag)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mousedata_group ON MouseData(Group_Number)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_group_cohort ON "Group"(Cohort_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_weights_eartag ON Weights(EarTag)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rotarod_eartag ON Rotarod(EarTag)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gripstrength_eartag ON GripStrength(EarTag)')

    conn.commit()
    conn.close()



if __name__ == '__main__':
    create_database()

# Example usage:
# survival_data = get_survival_data()
# draw_kaplan_meier_chart(survival_data)
