import models

def forward ():
    models.DB.create_tables([models.Request, models.Volunteer, models.Assignment])

if __name__ == '__main__':

    forward()
