stage = "test"

def get_db_info():

    if stage == "stag":
        return {
            "server": "host.docker.internal",
            "port": "5432",
            "user": "postgres",
            "password": "12345678",
            "database": "assetz2"
        }
    
    elif stage == "test":

        return {
            "server": "host.docker.internal",
            "port": "5432",
            "user": "postgres",
            "password": "12345678",
            "database": "assetz2"
        }
    
    elif stage == "prod":
        
        return {
            "server": "host.docker.internal",
            "port": "5432",
            "user": "postgres",
            "password": "12345678",
            "database": "assetz2"
        }
        