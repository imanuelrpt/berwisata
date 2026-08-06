"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    categories = op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("icon", sa.String(length=100), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=True)

    users = op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.String(length=1000), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "destinations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=False),
        sa.Column("province", sa.String(length=100), nullable=False),
        sa.Column("regency", sa.String(length=120), nullable=False),
        sa.Column("district", sa.String(length=120), nullable=True),
        sa.Column("village", sa.String(length=120), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("price_min", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_free", sa.Boolean(), nullable=False),
        sa.Column("currency", sa.String(length=5), nullable=False),
        sa.Column("opening_time", sa.String(length=5), nullable=True),
        sa.Column("closing_time", sa.String(length=5), nullable=True),
        sa.Column("is_open_24h", sa.Boolean(), nullable=False),
        sa.Column("days_open", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("popularity", sa.Integer(), nullable=False),
        sa.Column("visitor_count", sa.BigInteger(), nullable=False),
        sa.Column("facilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("safety", sa.Float(), nullable=False),
        sa.Column("cleanliness", sa.Float(), nullable=False),
        sa.Column("beauty", sa.Float(), nullable=False),
        sa.Column("road_access", sa.Float(), nullable=False),
        sa.Column("crowd_level", sa.Float(), nullable=False),
        sa.Column("hidden_gem_score", sa.Float(), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("website", sa.String(length=300), nullable=True),
        sa.Column("instagram", sa.String(length=300), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column("is_trending", sa.Boolean(), nullable=False),
        sa.Column("view_count", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_destinations_slug"), "destinations", ["slug"], unique=True)
    op.create_index("ix_destinations_geo", "destinations", ["latitude", "longitude"], unique=False)
    op.create_index(op.f("ix_destinations_province"), "destinations", ["province"], unique=False)
    op.create_index(op.f("ix_destinations_regency"), "destinations", ["regency"], unique=False)
    op.create_index(op.f("ix_destinations_rating"), "destinations", ["rating"], unique=False)
    op.create_index(op.f("ix_destinations_score"), "destinations", ["hidden_gem_score"], unique=False)
    op.create_index(op.f("ix_destinations_category_id"), "destinations", ["category_id"], unique=False)

    op.create_table(
        "destination_images",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("destination_id", sa.BigInteger(), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("caption", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_destination_images_destination_id"), "destination_images", ["destination_id"], unique=False)

    op.create_table(
        "favorites",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("destination_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "destination_id", name="uq_favorite_user_destination"),
    )
    op.create_index(op.f("ix_favorites_user_id"), "favorites", ["user_id"], unique=False)
    op.create_index(op.f("ix_favorites_destination_id"), "favorites", ["destination_id"], unique=False)

    op.create_table(
        "search_histories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=True),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_search_histories_user_id"), "search_histories", ["user_id"], unique=False)

    op.create_table(
        "user_locations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("tracked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_locations_user_id"), "user_locations", ["user_id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_token_hash"), "refresh_tokens", ["token_hash"], unique=True)

    op.create_table(
        "ratings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("destination_id", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "destination_id", name="uq_rating_user_destination"),
    )
    op.create_index(op.f("ix_ratings_user_id"), "ratings", ["user_id"], unique=False)
    op.create_index(op.f("ix_ratings_destination_id"), "ratings", ["destination_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ratings_destination_id"), table_name="ratings")
    op.drop_index(op.f("ix_ratings_user_id"), table_name="ratings")
    op.drop_table("ratings")
    op.drop_index(op.f("ix_refresh_tokens_token_hash"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_index(op.f("ix_user_locations_user_id"), table_name="user_locations")
    op.drop_table("user_locations")
    op.drop_index(op.f("ix_search_histories_user_id"), table_name="search_histories")
    op.drop_table("search_histories")
    op.drop_index(op.f("ix_favorites_destination_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_user_id"), table_name="favorites")
    op.drop_table("favorites")
    op.drop_index(op.f("ix_destination_images_destination_id"), table_name="destination_images")
    op.drop_table("destination_images")
    op.drop_index(op.f("ix_destinations_category_id"), table_name="destinations")
    op.drop_index(op.f("ix_destinations_score"), table_name="destinations")
    op.drop_index(op.f("ix_destinations_rating"), table_name="destinations")
    op.drop_index(op.f("ix_destinations_regency"), table_name="destinations")
    op.drop_index(op.f("ix_destinations_province"), table_name="destinations")
    op.drop_index("ix_destinations_geo", table_name="destinations")
    op.drop_index(op.f("ix_destinations_slug"), table_name="destinations")
    op.drop_table("destinations")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_table("categories")
