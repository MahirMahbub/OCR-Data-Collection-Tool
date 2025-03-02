import os
import time
from typing import List

import imageio
from fastapi.encoders import jsonable_encoder

from app.cruds.character import CharacterCrud
from app.cruds.class_label import ClassLabelCrud
from app.cruds.ocr_tools import OcrToolCrud
from app.custom_classes.ocr_character_seperator import OcrCharacterSeperator
from db import models
from db.database import SessionLocal
from db.schemas import CharacterCreate, OcrDataUpdate, ClassLabelCreate


class BaseJobManager(object):
    def __init__(self):
        self.db = SessionLocal()

    @staticmethod
    def execute():
        pass


class PrintJobManager(BaseJobManager):
    def __init__(self):
        super().__init__()

    def print_hello_activity(self, should_run):
        """Work Flow Start"""
        print("nabila")
        time.sleep(4)
        """Work Flow End"""

    @staticmethod
    def execute():
        PrintJobManager().print_hello_activity(should_run=True)


class PreOcrCharacterLoad(BaseJobManager):
    def __init__(self):
        super().__init__()

    def ocr_character_collection_activity(self, should_run):
        # preload_flag = self.db.query(models.Properties).filter(models.Properties.name == "CharacterDataPreLoad").first()
        # print(preload_flag)
        # if not preload_flag:
        current_path = os.getcwd()
        class_data_path = "/app/data/training_set/"
        list_dir = os.listdir(current_path + class_data_path)
        for class_name in list_dir:
            label_item = ClassLabelCreate(class_id=class_name)
            ClassLabelCrud(db=self.db).store(item=label_item, checker={"class_id": class_name})

            list_of_files = [current_path + class_data_path + os.path.join(class_name, f) for f in
                                 os.listdir(current_path + class_data_path + class_name + "/")]
            for file in list_of_files:
                item = CharacterCreate(character_path=file,
                                           class_id=class_name,
                                           is_labeled=True)
                CharacterCrud(db=self.db).store(item=item, checker={"character_path": file})
            # self.db.commit()
        self.db.add(models.Properties(name="CharacterDataPreLoad", value=True))
        self.db.commit()

    @staticmethod
    def execute():
        PreOcrCharacterLoad().ocr_character_collection_activity(should_run=True)


class CharacterExtractorManager(BaseJobManager):
    def __init__(self):
        super().__init__()

    def character_extract_activity(self, should_run):
        ocr_processing_object: OcrCharacterSeperator = OcrCharacterSeperator()
        ocr_image_paths: List[models.OcrData] = OcrToolCrud(db=self.db).get_by_non_extracted()
        print(ocr_image_paths)
        # print(os.getcwd())
        for ocr_image in ocr_image_paths:
            images_and_save_path = ocr_processing_object.character_extractor(ocr_image.file_path)
            for save_path, char_img in images_and_save_path:
                imageio.imwrite(save_path, char_img)
                item = CharacterCreate(character_path=save_path)
                character_model_object = CharacterCrud(db=self.db).store(jsonable_encoder(item))
                self.db.add(character_model_object)
            item = OcrDataUpdate(is_extracted=True)
            OcrToolCrud(db=self.db).update(id_=ocr_image.id, item=item)
            self.db.commit()

    @staticmethod
    def execute():
        CharacterExtractorManager().character_extract_activity(should_run=True)
