from datetime import date
from pydantic import BaseModel, ConfigDict, Field, model_validator


class UserSchema(BaseModel):

    id: int
    name: str

    model_config = ConfigDict(
        extra='ignore',
    )


class ClientSchema(UserSchema):

    workouts: int = Field(default=0, ge=0)


class TrainerSchema(UserSchema):

    time_zone: str


class WorkDaySchema(BaseModel):

    item: str
    work: str

    @model_validator(mode='after')
    def is_work(self):
        for work_item in self.work.split(','):  # str
            if work_item.isdigit() and -1 < int(work_item) < 24:
                continue
            raise ValueError('work is not valid')
        return self

    @model_validator(mode='after')
    def is_item(self):
        if isinstance(self.item, str) and 0 < int(self.item) < 4:
            return self
        raise ValueError('item is not valid')


class SelectedDateSchema(BaseModel):

    start: str
    stop: str
    breaks: str

    @model_validator(mode='after')
    def is_breaks(self):
        if self.breaks == 'нет':
            return self
        for item in self.breaks.split(','):  # str
            if item.isdigit() and 0 < int(item) < 24:
                continue
            raise ValueError('Breaks is not valid')
        return self


class ScheduleSchema(BaseModel):

    client_name: str = Field(default='no_name')
    client_id: int
    trainer_id: int
    date: date
    time: int = Field(ge=0, le=23)
