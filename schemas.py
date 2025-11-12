"""
Database Schemas for Community App

Define MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Collection name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    username: str = Field(..., description="Unique username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    bio: Optional[str] = Field(None, description="Short bio")
    is_active: bool = Field(True, description="Whether user is active")

class Post(BaseModel):
    author: str = Field(..., description="Username of the author")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content/body")
    tags: List[str] = Field(default_factory=list, description="Tags for the post")
    image_url: Optional[str] = Field(None, description="Optional image URL")

class Event(BaseModel):
    organizer: str = Field(..., description="Username of the organizer")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    location: str = Field(..., description="Event location")
    start_time: datetime = Field(..., description="Event start time (ISO)")
    end_time: Optional[datetime] = Field(None, description="Event end time (ISO)")

class Notification(BaseModel):
    user: Optional[str] = Field(None, description="Target username. None means broadcast to all")
    type: str = Field(..., description="Type of notification: post|event|info")
    message: str = Field(..., description="Notification message")
    related_id: Optional[str] = Field(None, description="Related document id as string")
    is_read: bool = Field(False, description="Whether the notification has been read")
