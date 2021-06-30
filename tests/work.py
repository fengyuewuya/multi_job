#coding=utf-8
import unittest
import os
import sys
sys.path.append("../SDK/")
from MultiJob import MultiJob
class MultiJobTest(unittest.TestCase):
    # 初始化操作 执行每个case都需要
    def setUp(self):
        #print("初始化操作 执行每个case都需要")
        pass

    # 测试用例执行完后 执行每个case后所需执行的操作
    def tearDown(self):
        #print("测试用例执行完后 执行每个case后所需执行的操作")
        pass

    # 所有case执行的前置条件 只执行一次
    @classmethod
    def setUpClass(cls):
        # 初始化 MultiJob
        cls.client = MultiJob("http://localhost:5006")
        #print("所有case执行的前置条件")
        pass

    # 所有case执行完成后执行一次
    @classmethod
    def tearDownClass(cls):
        #print("所有case执行完成后执行一次")
        pass

    # 测试是否有网络连接
    def test_get_all_job_type(self):
        result = self.client.get_all_job_type()
        self.assertTrue("code" in result)
        print("测试网络连接成功！")

    # 添加一个任务类型
    def test_update_job_file_status(self):
        result = self.client.update_job_file_status(job_type="test_job", job_path="jobs/test_job/")
        self.assertTrue("code" in result)
        self.assertTrue("data" in result)
        self.assertTrue("version" in result["data"])
        print("添加一个任务类型 test_job 成功, 当前任务版本为 %s !" % result['data']['version'])

    # 添加一个任务
    def test_insert_job(self):
        job_id = self.client.insert_job(job_type="test_job", data=1)
        self.assertTrue(job_id > 0)
        globals()['job_id'] = job_id
        print("添加一个任务成功，任务ID为%s!" % job_id)

    # 查看任务结果
    def test_get_job_detail(self):
        job_id = globals()['job_id']
        result = self.client.get_job_detail(job_id)
        self.assertTrue("code" in result)
        self.assertTrue("data" in result)
        self.assertTrue(result['data']['id'] == job_id)
        print("查看任务的详细结果成功!")

    # 查看 任务列表成功
    def test_get_job_list(self):
        result = self.client.get_job_list(job_type='test_job')
        self.assertTrue("code" in result)
        self.assertTrue("data" in result)
        self.assertTrue(len(result['data']) >= 0)
        print("查看任务列表成功!")

    # 查看任务 summary 结果成功
    def test_get_job_summary(self):
        result = self.client.get_job_summary(job_type="test_job", batch=-1)
        print(result)
        self.assertTrue("code" in result)
        self.assertTrue("data" in result)
        self.assertTrue(len(result['data']) >= 0)
        print("查看任务 summary 结果成功!")

    # 下载云端的任务文件 到本地
    def test_load_job_file_from_server(self):
        result = self.client.load_job_file(job_type="test_job")
        self.assertTrue(result == 1)
        self.client.main({"seed":1})
        print("加载云端 test_job 任务到本地跑，成功!")

    # 加载本地任务文件
    def test_load_job_file_from_local(self):
        job_path = "jobs/test_job"
        result = self.client.load_job_file(job_path=job_path)
        self.assertTrue(result == 1)
        self.client.main({"seed":1})
        print("加载本地任务文件跑，成功!")

    # 测试 stock_data
    def test_crawl_stock_data(self):
        # 插入新的任务类型
        job_type = "crawl_stock_data"
        result = self.client.update_job_file_status(job_type=job_type, job_path="jobs/crawl_stock_data/")
        # 插入任务
        job_id = self.client.insert_job(job_type=job_type, stock_id="sz000829", time_sep=30, time_length=1)
        self.assertTrue(job_id > 0)
        globals()['job_id'] = job_id
        print("添加 爬虫 测试任务成功，任务ID为%s!" % job_id)
        return 1

    # 测试 stock_data
    def test_save_stock_data(self):
        save_dir = os.path.join(os.getcwd(), "stock_data")
        # 将存放地址放在文件中
        with open('jobs/save_stock_data/dir', 'w') as w:
            w.write(save_dir)
        os.makedirs(save_dir, exist_ok=True)
        # 插入新的任务类型
        job_type = "save_stock_data"
        result = self.client.update_job_file_status(job_type=job_type, job_path="jobs/save_stock_data/")
        # 设定任务的tag， batch、priority, limit_count 等信息
        self.client.set_tag("test")
        self.client.set_batch("test")
        self.client.set_priority(1)
        self.client.set_limit_count(3)
        # 插入一条任务
        job_id = self.client.insert_job(job_type=job_type, stock_id="sz000829", time_sep=30, time_length=1)
        self.assertTrue(job_id > 0)
        globals()['job_id'] = job_id
        print("添加 爬虫 测试任务成功，任务ID为%s!" % job_id)
        return 1

    @unittest.skip("do't run as not ready")
    def test_4(self):
        pass

    @unittest.skipIf(1>0, "1 > 0所以不能够执行")
    def test_5(self):
        pass

    @unittest.skipUnless(2==2, "2=2所以能够执行")
    def test_6(self):
        print("2==2 所以能够执行")
        pass

if __name__ == "__main__":
    # verbosity, 默认是1; 成功是. ; 失败是 F; 出错是E; 跳过是 S
    # verbosity = 0 不输出每个用例的结果
    # verbosity = 2 输出详细的执行报告
    # unittest.main(verbosity=1)
    suite = unittest.TestSuite()
    # 简单测试用例
    suite.addTest(MultiJobTest("test_get_all_job_type"))
    suite.addTest(MultiJobTest("test_update_job_file_status"))
    suite.addTest(MultiJobTest("test_insert_job"))
    suite.addTest(MultiJobTest("test_get_job_detail"))
    suite.addTest(MultiJobTest("test_get_job_list"))
    suite.addTest(MultiJobTest("test_get_job_summary"))
    suite.addTest(MultiJobTest("test_load_job_file_from_server"))
    suite.addTest(MultiJobTest("test_load_job_file_from_local"))
    # 跑进阶 crawl_stock_data
    suite.addTest(MultiJobTest("test_crawl_stock_data"))
    # 跑复杂用例 save_stock_data
    suite.addTest(MultiJobTest("test_save_stock_data"))
    # 开始跑测试用例
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

