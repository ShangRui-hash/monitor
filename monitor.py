#!/usr/bin/python3
# -*- coding:utf-8 -*-
# @Author : 小艾

import os
import time
from io import BytesIO
import xlwt

from Functions.Commons.excel import sheet_init, excel_sheet_processor, sheet_init_ms
from Functions.Commons.excel_html import  list_diction_to_html_ms, list_diction_to_html_cnnvd, save_dom_to_html_cnnvd, save_dom_to_html_ms
from Functions.Commons.wechat_api import wechat_qiye
from Functions.RequestInfo.cnnvd_monitor import *
from Functions.Sql.sql_helper import *
from Functions.Commons.github import getNews
from Functions.Commons.mail import *
from Functions.Commons.translate import get_cve_des_zh, translate
from Functions.RequestInfo.github_monitor import wechat_data
from Functions.RequestInfo.MS_monitor import getMSDATA, wechat_MS

github_headers = {
    'Authorization': "ghp_Znu***********************5Pt2KhQqN"  # 替换自己的github token     https://github.com/settings/tokens/new
}
last_total_count = 0
#保存文件的路径
dir_mon = "/usr/share/nginx/html/download/"
#主函数
def main():
    excel_row = 1
    try:
        while True:
            file_path = dir_mon
            today_time_cnnvd = str(datetime.datetime.now().date()) + "_cnnvd"
            fileName = file_path + today_time_cnnvd + '.xls'
            if os.path.isfile(fileName):
                excel_row = excel_row
            else:
                excel_row = 1
            file = open(fileName, mode='ab')#在硬盘上创建EXCEL文件
            stream = BytesIO() # 打开数据流
            f = xlwt.Workbook()  # 创建EXCEL工作簿
            sheet1 = sheet_init(f) # 初始化工作
            pageNo = 1
            flag = False #该标志用于控制是否继续请求CNNVD下一页的数据
            send_msg_flag = False #该标志用于控制是否需要向微信推送消息
            if is_database_empty():
                flag = True
            #print(danger_level_nums()[0])
            #print(danger_level_nums()[1])
            #quit(0)
            #该while循环是操作cnnvd的。
            while True:
                url = 'http://www.cnnvd.org.cn/web/vulnerability/querylist.tag?pageno=' + str(pageNo) + '&repairLd='
                header = {
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.80 Safari/537.36',
                    'Connection': 'keep-alive',
                }
                try:
                    r = requests.get(url, headers=header, timeout=30)
                except Exception as e:
                    print('连接超时。。。')
                    break
                html = BeautifulSoup(r.text, 'html.parser')
                links = html.find_all(class_='a_title2')
                for link in links:
                    try:
                        k = str(link.attrs['href'])
                        one = getURLDATA("http://www.cnnvd.org.cn" + k)  # 获取每一个单独漏洞的详细信息页面
                        values = "'" + one[0] + "'"
                        #print(values)
                        if is_not_exist(one):
                            for i in range(1, len(one)):
                                values = values + "," + "'" + one[i] + "'"
                                sheet1.write(excel_row, i - 1 , one[i - 1])
                            excel_row = excel_row + 1
                            insertTo(values)
                           # print(values)
                           # pageNo = pageNo + 1
                            send_msg_flag = True
                        else:
                            pageNo = 1
                            flag = True
                            break
                    except Exception as e:
                        print("http://www.cnnvd.org.cn" + k)
                        break
                if flag:
                    f.save(stream)  # 保存数据到内存中
                    value = stream.getvalue() #从内存中取出数据
                    file.write(value) #将数据写入硬盘中的文件
                    file.close() #关闭文件流
                    #打开生成的xls文件
                    print(dir_mon + str(today_time_cnnvd) + '.xls')
                    filepath = os.path.abspath(dir_mon + str(today_time_cnnvd) + '.xls')
                    #解析生成的xls
                    list_work = excel_sheet_processor(filepath)
                    if list_work:
                        #生成HTML格式
                        dom = list_diction_to_html_cnnvd(list_work)
                        #保存到文件
                        save_dom_to_html_cnnvd(dom)

                    if send_msg_flag:
                        # server(str(datetime.datetime.now().date())+"的最新CNNVD信息推送：","EXCEL文件下载位置")

                        lever_test = str(danger_level_nums())
                        # 周五推送危险等级数量
                        data = wechat_cnnvd(lever_test)
                        print(lever_test,data)
                        # 推送微信
                        wechat_qiye(data[0])
                        #推送邮箱
                        #dom = list_diction_to_html_cnnvd(list_work)
                        #取出要发送的链接
                        data_mail =data[2]
                        # 推送邮箱
                        #main_user(str(data_mail))
                        send_msg_flag = False
                    pageNo = 1 #重置页数
                    flag = False
                    break #跳出内层While
                else:
                    pageNo = pageNo + 1
            file_path_ms = dir_mon
            today_time_ms = str(datetime.datetime.now().date()) + "_ms"
            fileNameMS = file_path_ms + today_time_ms + '.xls'
            if os.path.isfile(fileNameMS):
                excel_row = excel_row
            else:
                excel_row = 1
            file_ms = open(fileNameMS, mode='ab')#在硬盘上创建EXCEL文件
            stream_ms = BytesIO() # 打开数据流
            f_ms = xlwt.Workbook()  # 创建EXCEL工作簿
            sheet1_ms = sheet_init_ms(f_ms) # 初始化工作
            ms_url = 'https://api.msrc.microsoft.com/sug/v2.0/zh-CN/vulnerability'
            wechat_is_flag = False
            for cve_nums in range(0, 20):
                try:
                    one_ms = getMSDATA(ms_url, cve_nums)
                except Exception  as e:
                    print('连接超时。。。')
                    break
                #print(one_ms)
                values_ms = "'" + one_ms[0] + "'"
                #print(values_ms)
                if is_not_exist_ms(one_ms):
                    for i in range(1, len(one_ms)):
                        values_ms = values_ms + "," + "'" + one_ms[i] + "'"
                        sheet1_ms.write(excel_row, i-1 , one_ms[i-1])
                    excel_row = excel_row + 1
                    #插入数据库
                    insertToMS(values_ms)
                    wechat_is_flag = True
            if wechat_is_flag:
                #推送微信
                data = wechat_MS()
                data_ms = data[0]
                print(data_ms)
                wechat_qiye(data_ms)
                # 取出要发送的链接
                data_mail = data[2]
                #推送邮箱
                #main_user(str(data_mail))
                wechat_is_flag = False
            f_ms.save(stream_ms)  # 保存数据到内存中
            value_ms = stream_ms.getvalue()  # 从内存中取出数据
            file_ms.write(value_ms)  # 将数据写入硬盘中的文件
            file_ms.close()  # 关闭文件流
            # 打开生成的xls文件
            print(dir_mon + str(today_time_ms) + '.xls')
            filepath = os.path.abspath(dir_mon + str(today_time_ms) + '.xls')
            # 解析生成的xls
            list_work = excel_sheet_processor(filepath)
            if list_work:
                # 生成HTML格式
                dom = list_diction_to_html_ms(list_work)
                # 保存到文件
                save_dom_to_html_ms(dom)
            print("cve监控中 ...")
            # 抓取本年的cve
            year = datetime.datetime.now().year
            api = "https://api.github.com/search/repositories?q=CVE-{}&sort=updated".format(year)
            # 请求API
            req = requests.get(api, headers=github_headers, timeout=10).json()
            total_count = req['total_count']
            print(total_count)

            print(req['items'][0]['name'])
            global last_total_count

            if total_count != last_total_count:
                # 推送正文内容
                # 推送标题
                last_total_count = total_count
                text = '新的CVE信息'
                # 获取 cve 名字 ，根据cve 名字，获取描述，并翻译
                cve_name = req['items'][0]['name']
                print(cve_name)
                cve_zh = get_cve_des_zh(cve_name)
                msg = "CVE编号：" + cve_name + "\r\n" + "CVE描述：" + cve_zh
                url = req['items'][0]['html_url']
                print(url)
                # url2 = getNews()[0]
                # 推送微信
                data = wechat_data(text, msg, url)
                wechat_qiye(data)
            time.sleep(60*60*24) #设置定时，每24小时查看一次

    except KeyboardInterrupt:
        log_update_time = str(datetime.datetime.now().ctime())
        shutdown_msg = "[x] 程序人为停止!!"
        write_log(log_update_time,msg = shutdown_msg)
        print('程序已停止')

if __name__ == "__main__":
    last_total_count = getNews()[0]
    main()
