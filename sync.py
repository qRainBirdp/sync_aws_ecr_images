#! /usr/bin/env python
# coding=utf-8
# @Time    : 2021/12/14
# @Author  : Rainbird
# @Email   : xbrainbird@gmail.com
# @Describe: Syncing images between different regions

import os, logging, boto3
from collections import Counter
from time import sleep
from botocore.config import Config

TARGET = {"region": "string",
      "access_key_id": "string",
      "secret_access_key": "string"}
MAIN = {"region": "string",
       "access_key_id": "string",
       "secret_access_key": "string"}

logging.getLogger().setLevel(logging.INFO)

class Region:
    def __init__(self, region):
        self.region = region
        region_config = Config(region_name=region["region"])
        self.client = boto3.client(
            'ecr',
            aws_access_key_id=region["access_key_id"],
            aws_secret_access_key=region["secret_access_key"],
            config=region_config)
        self.res = {}
        self.uri = ""

    def get_repository_list(self):
        logging.info("Start scanning the image list from {}.".format(self.region['region']))
        res = self.client.describe_repositories()['repositories']
        for i in range(len(res)):
            if i == 0:
                uri = res[i]['repositoryUri']
                uri = uri.split('/')
                self.uri = uri[0]
            name = res[i]['repositoryName']
            image_response = self.client.list_images(
                repositoryName=name,
            )
            image = image_response['imageIds']
            image_list = []
            for j in range(len(image)):
                try:
                    image[j]['imageTag']
                except KeyError:
                    continue
                else:
                    image_list.append(image[j]['imageTag'])
            self.res[name] = image_list
        logging.info("Get the image list from {} successfully.".format(self.region['region']))



class Sync:
    def __init__(self, region_main, region_target):
        self.main_res = region_main
        self.target_res = region_target
        self.sync = True

    def check(self):
        logging.info("Start comparing two repository.")
        for i in self.main_res.res:
            if i in self.target_res.res:
                main_list = Counter(self.main_res.res[i])
                target_list = Counter(self.target_res.res[i])
                lack = list((main_list - target_list).elements())
                if len(lack) == 0:
                    logging.info("{} has been synchronized,skip this repository.".format(i))
                    continue
                else:
                    logging.info("{}'s unsynchronized image version is {}".format(i, lack))
                    logging.info("Start syncing all images from {}.".format(i))
                    self.sync_image(i, lack)
                    if self.sync:
                        self.sync = False
            else:
                logging.info("Unsynchronized repository is {}".format(i))
                lack = self.main_res.res[i]
                logging.info("Start creating a repository named {}.".format(i))
                self.create_repository(i)
                logging.info("{}'s unsynchronized image version is {}".format(i, lack))
                logging.info("Start syncing all images from {}.".format(i))
                self.sync_image(i, lack)
                if self.sync:
                    self.sync = False

    def sync_image(self, res, lack):
        for i in lack:
            sleep(5)
            logging.info("---------- Logging ----------")
            self.login_aws(True)
            image_pull = self.main_res.uri + '/' + res + ':' + i
            logging.info("---------- Pulling ----------")
            self.pull_image(image_pull)
            logging.info("---------- Logging ----------")
            self.login_aws(False)
            image_push = self.target_res.uri + '/' + res + ':' + i
            logging.info("---------- Pushing ----------")
            self.push_image(image_push, image_pull)
            logging.info("---------- Cleaning ----------")
            self.clean_image(image_push, image_pull)

    def is_synchronized(self):
        if self.sync:
            return True
        else:
            return False

    def create_repository(self, res):
        response = self.target_res.client.create_repository(
            repositoryName=res,
            imageTagMutability='MUTABLE',
            imageScanningConfiguration={
                'scanOnPush': False
            },
        )
        logging.info("Create repository successfully.")
        return response

    def login_aws(self, mode):
        if mode:
            os.system(
                "aws ecr get-login-password --region {} --profile {} | docker login --username AWS --password-stdin {}".format(
                    self.main_res.region['region'], self.main_res.region['region'], self.main_res.uri))
        else:
            os.system(
                "aws ecr get-login-password --region {} --profile {} | docker login --username AWS --password-stdin {}".format(
                    self.target_res.region['region'], self.target_res.region['region'], self.target_res.uri))

    @staticmethod
    def pull_image(image):
        fail_pull = 0
        while fail_pull < 3:
            try:
                os.system("docker pull {}".format(image))
                logging.info("Pull {} successfully".format(image))
                break
            except:
                fail_pull += 1
                if fail_pull == 3:
                    logging.error("Pull {} failed".format(image))
                    break

    @staticmethod
    def push_image(image_push, image_pull):
        fail_push = 0
        os.system("docker tag {} {}".format(image_pull, image_push))
        while fail_push < 3:
            try:
                os.system("docker push {}".format(image_push))
                logging.info("Push {} successfully".format(image_push))
                break
            except:
                fail_push += 1
                if fail_push == 3:
                    logging.error("Push {} failed".format(image_push))
                    break

    @staticmethod
    def clean_image(image_push, image_pull):
        fail_clean = 0
        while fail_clean < 3:
            try:
                os.system("docker rmi {}".format(image_push))
                os.system("docker rmi {}".format(image_pull))
                logging.info("Clean {} successfully".format(image_push))
                break
            except:
                fail_clean += 1
                if fail_clean == 3:
                    logging.error("Clean {} failed".format(image_push))
                    break


if __name__ == '__main__':
    target = Region(TARGET)
    target.get_repository_list()
    main = Region(MAIN)
    main.get_repository_list()
    check = Sync(region_main=main, region_target=target)
    check.check()
    if check.is_synchronized():
        logging.info("Target ecr repository has been synchronized with main ecr repository.")
    else:
        check.check()
        if check.is_synchronized():
            logging.info("Target ecr repository has been synchronized with main ecr repository.")
        else:
            logging.error("Something wrong when syncing the images.")

