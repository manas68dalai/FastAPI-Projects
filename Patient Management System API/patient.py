from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()

## Pydantic Model for insert/create a new data 

class Patient(BaseModel):
    id: Annotated[str, Field(..., description="ID of the patient", examples=["P001"])]
    name: Annotated[str, Field(..., description="Name of the Patient", examples=["Manas Dalai"])]
    city: Annotated[str, Field(..., description="Enter the city where the patient is living", examples=["Bhubaneswar"])]
    age: Annotated[int, Field(..., gt=0, description="age of the patient")]
    gender: Annotated[Literal["male","female","others"], Field(..., description="gender of the patient")]
    height: Annotated[float, Field(..., gt=0, description="height of the patient in mtrs")]
    weight: Annotated[float, Field(..., gt=0, description="weight of the patient in kgs")]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 30:
            return "Normal"
        else:
            return "Obese"
        
## Pydantic model for Updation of data

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male','female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]


## Load the dataset

def load_data():
    with open('patients.json', 'r') as f:
        data = json.load(f)
    return data

## save the dataset

def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data, f)


@app.get("/")
def home():
    return {"message": "Patient Managment System API"}

@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient records"}

@app.get("/view")
def view():
    data = load_data()
    return data

@app.get("/patient/{patient_id}")
def view_patient(patient_id: str = Path(..., description= 'ID of the patient in the databaase', example='P001')):
    # load all the patient data
    data = load_data()

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code= 404, detail='patient not found')

@app.get('/sort')
def sort_patient(sort_by: str = Query(..., description= 'sort on the basis of height, weight or bmi'), order: str = Query("asc", description= 'sort in asc or desc order')):

    valid_fields = ["height", "weight", "bmi"]

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail= f"invalid field select from  {valid_fields}")
    if order not in ["asc","desc"]:
        raise HTTPException(status_code=400, detail="invalid order select between asc and desc")
    
    data = load_data()

    sort_order = True if order == "desc" else False

    sorted_data = sorted(data.values(), key=lambda x: x.get(sort_by,0), reverse= sort_order)

    return sorted_data

## Add/create new data in Dataset/server

@app.post("/create")
def create_patient(patient: Patient):

    # load the existing data
    data = load_data()

    # check if the patient already exist
    if patient.id in data:
        raise HTTPException(status_code=400, detail="patient already exists")
    
    # new patient add to the database
    data[patient.id] = patient.model_dump(exclude=["id"])

    # save into the json file
    save_data(data)

    return JSONResponse(status_code=201, content={"message":"patient created successfully"})


## Update the data in existing dataset

@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):

    #load the exist data
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="patient not found")
    
    existing_patient_info = data[patient_id]

    # convert the new input data into dictionary
    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    # updating the new given data in the existed data
    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    # existing_patient_info -> pydantic object -> updated bmi + verdict
    existing_patient_info['id'] = patient_id
    patient_pydantic_object = Patient(**existing_patient_info)

    # pydantic object -> dict
    existing_patient_info = patient_pydantic_object.model_dump(exclude='id')

    # add this dict to data
    data[patient_id] = existing_patient_info

    # save the data
    save_data(data)

    return JSONResponse(status_code=200, content={"message":"patient updated successfully"})

## delete the data

@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    # load the data
    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail="patient not found")
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200, content={"message":"patient deleted successfully"})