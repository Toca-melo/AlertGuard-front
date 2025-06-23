def userEntity(item) -> dict:
    return{
        "idVideo": item["idVideo"],
        "nombreVideo": item["nombreVideo"],
        "url": item["url"],
        "anomalia": item["anomalia"]
    }

def usersEntity(entity) -> list:
    [userEntity(item) for item in entity]