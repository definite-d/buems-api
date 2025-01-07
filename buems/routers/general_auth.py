# Pydantic schemas for requests and responses
# class UserCreate(BaseModel):
#     first_name: str
#     last_name: str
#     email: str
#     password: str
#
# class UserUpdate(BaseModel):
#     first_name: Optional[str] = None
#     last_name: Optional[str] = None
#     email: Optional[str] = None
#     is_active: Optional[bool] = None
#     is_verified: Optional[bool] = None
#

# @router.post("/users/", response_model=User)
# def create_user(user: UserCreate, db: Annotated[Session, Depends(db_dependency)]):
#     """
#     Create a new user.
#     """
#     try:
#         hashed_password = get_password_hash(user.password)
#         new_user = User(
#             first_name=user.first_name,
#             last_name=user.last_name,
#             email=user.email,
#             hashed_password=hashed_password,
#             user_type_id=UserTypeEnum.STUDENT,
#         )
#         created_user = create_user(db, new_user)
#         logger.info("User created with email {}", user.email)
#         return created_user
#     except Exception as e:
#         logger.error("Error creating user: {}", e)
#         raise HTTPException(status_code=400, detail="Failed to create user")
#
# @router.get("/users/{user_id}", response_model=User)
# def read_user(user_id: int, db: Annotated[Session, Depends(db_dependency)]):
#     """
#     Read a user's data.
#     """
#     try:
#         return get_user(db, user_id)
#     except UserNotFound:
#         logger.error("User with ID {} not found", user_id)
#         raise HTTPException(status_code=404, detail="User not found")
#
# @router.patch("/users/{user_id}", response_model=User)
# def update_user_endpoint(user_id: int, updates: UserUpdate, db: Annotated[Session, Depends(db_dependency)]):
#     """
#     Update an existing user.
#     """
#     try:
#         updated_user = update_user(db, user_id, **updates.model_dump(exclude_unset=True))
#         logger.info("Updated user with ID {}", user_id)
#         return updated_user
#     except UserNotFound:
#         logger.error("User with ID {} not found", user_id)
#         raise HTTPException(status_code=404, detail="User not found")
#     except Exception as e:
#         logger.error("Error updating user: {}", e)
#         raise HTTPException(status_code=400, detail="Failed to update user")
#
# @router.delete("/users/{user_id}")
# def delete_user_endpoint(user_id: int, db: Annotated[Session, Depends(db_dependency)]):
#     """
#     Delete a specific user.
#     """
#     try:
#         delete_user(db, user_id)
#         logger.info("Deleted user with ID {}", user_id)
#         return {"msg": "User deleted successfully"}
#     except UserNotFound:
#         logger.error("User with ID {} not found", user_id)
#         raise HTTPException(status_code=404, detail="User not found")
#
