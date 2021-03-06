from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, validators

from app.config import (
    PADDLE_VENDOR_ID,
    PADDLE_MONTHLY_PRODUCT_ID,
    PADDLE_YEARLY_PRODUCT_ID,
    URL,
    ADMIN_EMAIL,
)
from app.dashboard.base import dashboard_bp
from app.email_utils import send_email
from app.extensions import db
from app.models import LifetimeCoupon


class CouponForm(FlaskForm):
    code = StringField("Coupon Code", validators=[validators.DataRequired()])


@dashboard_bp.route("/lifetime_licence", methods=["GET", "POST"])
@login_required
def lifetime_licence():
    # sanity check: make sure this page is only for free user
    if current_user.lifetime_or_active_subscription():
        flash("You are already a premium user", "warning")
        return redirect(url_for("dashboard.index"))

    coupon_form = CouponForm()

    if coupon_form.validate_on_submit():
        code = coupon_form.code.data

        coupon = LifetimeCoupon.get_by(code=code)

        if coupon and coupon.nb_used > 0:
            coupon.nb_used -= 1
            current_user.lifetime = True
            db.session.commit()

            # notify admin
            send_email(
                ADMIN_EMAIL,
                subject=f"User {current_user.id} used lifetime coupon. Coupon nb_used: {coupon.nb_used}",
                plaintext="",
                html="",
            )

            flash("You are upgraded to lifetime premium!", "success")
            return redirect(url_for("dashboard.index"))

        else:
            flash(f"Code *{code}* expired or invalid", "warning")

    return render_template("dashboard/lifetime_licence.html", coupon_form=coupon_form)
