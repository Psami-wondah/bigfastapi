import fastapi as _fastapi
from fastapi.openapi.models import HTTPBearer
import fastapi.security as _security
import sqlalchemy.orm as _orm
from bigfastapi.utils import settings as settings
from bigfastapi.db import database as _database
from . import models as _models
from .models import user_models
from uuid import uuid4
from fastapi import BackgroundTasks
from .auth import create_passwordreset_token, create_verification_token
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from .auth import create_forgot_pasword_code, create_verification_code

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=settings.TEMPLATE_FOLDER,
)


async def get_user_by_email(email: str, db: _orm.Session):
    return db.query(user_models.User).filter(user_models.User.email == email).first()



async def send_code_password_reset_email(email: str, db: _orm.Session, codelength:int=None):
    user = await get_user_by_email(email, db)
    if user:
        code = await create_forgot_pasword_code(user, codelength)
        message = MessageSchema(
            subject="Password Reset",
            recipients=[email],
            template_body={
                "title": "Change your password",
                "first_name": user.first_name,
                "code": code["code"],
            },
            subtype="html",
        )
        await send_email_async(message, settings.PASSWORD_RESET_TEMPLATE)
        return {"code": code["code"]}
    else:
        raise _fastapi.HTTPException(status_code=401, detail="Email not registered")

async def resend_code_verification_mail(email: str, db: _orm.Session, codelength:int=None):
    user = await get_user_by_email(email, db)
    if user:
        code = await create_verification_code(user, codelength)
        message = MessageSchema(
            subject="Email Verification",
            recipients=[email],
            template_body={
                "title": "Verify Your Account",
                "first_name": user.first_name,
                "code": code["code"],
            },
            subtype="html",
        )
        await send_email_async(message, settings.EMAIL_VERIFICATION_TEMPLATE)
        return {"code": code["code"]}
    else:
        raise _fastapi.HTTPException(status_code=401, detail="Email not registered")


async def send_token_password_reset_email(email: str,redirect_url: str, db: _orm.Session):
    user = await get_user_by_email(email, db)
    if user:
        token = await create_passwordreset_token(user)
        path = "{}/?token={}".format(redirect_url, token["token"])
        message = MessageSchema(
            subject="Password Reset",
            recipients=[email],
            template_body={
                "title": "Change you",
                "first_name": user.first_name,
                "path": path,
            },
            subtype="html",
        )
        await send_email_async(message, settings.PASSWORD_RESET_TEMPLATE)
        return {"token": token}
    else:
        raise _fastapi.HTTPException(status_code=401, detail="Email not registered")



async def resend_token_verification_mail(email: str,redirect_url: str, db: _orm.Session):
    user = await get_user_by_email(email, db)
    if user:
        token = await create_verification_token(user)
        path = "{}/?token={}".format(redirect_url, token["token"])
        message = MessageSchema(
            subject="Email Verification",
            recipients=[email],
            template_body={
                "title": "Verify Your Account",
                "first_name": user.first_name,
                "path": path,
            },
            subtype="html",
        )
        await send_email_async(message, settings.EMAIL_VERIFICATION_TEMPLATE)
        return {"token": token}
    else:
        raise _fastapi.HTTPException(status_code=401, detail="Email not registered")


async def send_email_async(message: MessageSchema, template: str):
    fm = FastMail(conf)
    await fm.send_message(message, template_name=template)


def send_email_background(
    background_tasks: BackgroundTasks, message: MessageSchema, template: str
):
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message, template_name="email.html")
