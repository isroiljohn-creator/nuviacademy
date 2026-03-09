
    # --- Monthly Menu Logic ---

    def get_menu_template(self, profile_key):
        with get_sync_db() as session:
            return session.query(MenuTemplate).filter(MenuTemplate.profile_key == profile_key).first()

    def create_menu_template(self, profile_key, menu_json, shopping_list_json):
        with get_sync_db() as session:
            template = MenuTemplate(
                profile_key=profile_key,
                menu_json=menu_json,
                shopping_list_json=shopping_list_json
            )
            session.add(template)
            session.commit()
            return template.id

    def get_user_menu_link(self, user_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return None
            
            link = session.query(UserMenuLink).filter(
                UserMenuLink.user_id == pk,
                UserMenuLink.is_active == True
            ).first()
            
            # Eager load template
            if link:
                session.refresh(link)
                # We need to load template content here or handle it carefully
                # Since session closes, we return a dict or detached object if possible
                # But sqlalchemy objects detach. Let's return the object ID and data needed.
                # Actually, simplest is to return the link object but accessing relationships might fail if session closed.
                # Let's return a simple dict for safety
                
                # Fetch template manually
                template = session.query(MenuTemplate).filter(MenuTemplate.id == link.menu_template_id).first()
                
                return {
                    "id": link.id,
                    "menu_template_id": link.menu_template_id,
                    "current_day_index": link.current_day_index,
                    "start_date": link.start_date,
                    "menu_json": template.menu_json if template else "[]",
                    "shopping_list_json": template.shopping_list_json if template else "[]"
                }
            return None

    def create_user_menu_link(self, user_id, template_id):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            
            # Deactivate old links
            session.query(UserMenuLink).filter(UserMenuLink.user_id == pk).update({"is_active": False})
            
            link = UserMenuLink(
                user_id=pk,
                menu_template_id=template_id,
                current_day_index=1,
                is_active=True
            )
            session.add(link)
            session.commit()

    def update_menu_day(self, user_id, new_day_index):
        with get_sync_db() as session:
            pk = self._get_user_pk(session, user_id)
            if not pk: return
            
            link = session.query(UserMenuLink).filter(
                UserMenuLink.user_id == pk,
                UserMenuLink.is_active == True
            ).first()
            
            if link:
                # Clamp between 1 and 30
                new_day_index = max(1, min(30, new_day_index))
                link.current_day_index = new_day_index
                session.commit()
                return new_day_index
            return 1
