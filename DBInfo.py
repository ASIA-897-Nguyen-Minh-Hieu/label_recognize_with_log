stage = "test"

def get_db_info():

    if stage == "stag":
        return {
            "server": "192.168.5.209",
            "port": "5432",
            "user": "postgres",
            "password": "postgres",
            "database": "assetz2"
        }
    
    elif stage == "test":

        return {
            "server": "192.168.5.209",
            "port": "5432",
            "user": "postgres",
            "password": "postgres",
            "database": "assetz2"
        }
    
    elif stage == "prod":
        
        return {
            "server": "192.168.5.209",
            "port": "5432",
            "user": "postgres",
            "password": "postgres",
            "database": "assetz2"
        }
        