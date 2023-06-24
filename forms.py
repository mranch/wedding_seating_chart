from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, RadioField, IntegerField, TextAreaField, TelField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

from model import Sex, Side


class GuestForm(FlaskForm):
    name = StringField("Ім'я", validators=[DataRequired()])
    profile_image = FileField("Фото", validators=[Optional()])
    sex = RadioField("Стать", choices=[sex.value for sex in Sex], default="Невідомо")
    age = IntegerField("Вік", validators=[Optional(), NumberRange(min=1, max=100, message="Введіть реальний вік!")],
                       default=18)
    description = TextAreaField("Опис", validators=[Optional()])
    phone_number = TelField("Номер телефону", validators=[Optional()], render_kw={"pattern": r"(((\+)?3)?8)?\d{10}"})
    contact = TextAreaField("Інша контактна інформація", validators=[Optional()])
    table_number = SelectField("Номер столу", choices=["--"] + list(range(1, 6)))
    seat_number = SelectField("Номер місця", choices=["--"] + list(range(1, 12)))
    side = RadioField("Сторона", choices=[side.value for side in Side], default="Наречені")


class GuestEditForm(GuestForm):
    delete = SubmitField("Видалити гостя")
    cancel = SubmitField("Відмінити")
