import json
import random
import time
import pandas as pd
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService

def get_driver(browser_name):
    if browser_name.lower() == "chrome":
        service = ChromeService(executable_path="D:\\path\\to\\chromedriver.exe")
        return webdriver.Chrome(service=service)
    elif browser_name.lower() == "edge":
        service = EdgeService(executable_path=r"E:\edgedriver_win64\msedgedriver.exe")
        return webdriver.Edge(service=service)
    elif browser_name.lower() == "firefox":
        service = FirefoxService(executable_path="D:\\path\\to\\geckodriver.exe")
        return webdriver.Firefox(service=service)
    elif browser_name.lower() == "safari":
        return webdriver.Safari()
    else:
        raise ValueError("Unsupported browser")

def random_scroll_and_wait(driver):
    """执行随机滚动和等待"""
    scroll_distance = random.randint(400, 800)
    driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
    time.sleep(random.uniform(2, 4))

def extract_job_data(job_element):
    try:
        job_name = job_element.find_element(By.CSS_SELECTOR, ".jname.text-cut").text
    except:
        job_name = "未知"

    try:
        job_location = job_element.find_element(By.CSS_SELECTOR, ".br .area .shrink-0").text
    except:
        job_location = "未知"

    try:
        sensors_data = job_element.find_element(By.CSS_SELECTOR, '[sensorsname="JobShortExposure"]').get_attribute(
            "sensorsdata")
        job_experience = json.loads(sensors_data.replace("&quot;", "\"")).get("jobYear", "未知")
    except:
        job_experience = "未知"

    try:
        salary = job_element.find_element(By.CSS_SELECTOR, ".sal.shrink-0").text
    except:
        salary = "未知"

    try:
        company_name = job_element.find_element(By.CSS_SELECTOR, ".cname.text-cut").text
    except:
        company_name = "未知"

    company_details = job_element.find_elements(By.CSS_SELECTOR, ".dc.text-cut")
    company_industry = company_details[0].text if len(company_details) > 0 else "未知"
    company_nature = company_details[1].text if len(company_details) > 1 else "未知"
    company_size = company_details[2].text if len(company_details) > 2 else "未知"

    try:
        tags = [tag.text for tag in job_element.find_elements(By.CSS_SELECTOR, ".tags .tag")]
        tags = tags if tags else ["无"]
    except:
        tags = ["无"]

    return {
        "岗位名称": job_name,
        "工作地点": job_location,
        "工作经验": job_experience,
        "薪资": salary,
        "公司名称": company_name,
        "公司行业": company_industry,
        "公司性质": company_nature,
        "公司规模": company_size,
        "岗位描述": tags
    }

def crawl(driver, key):
    jobs_data = []
    try:
        driver.get("https://www.51job.com/")

        random_scroll_and_wait(driver)

        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//p[@class='ipt']/input[@id='kwdselectid']"))
        )

        search_box.clear()
        search_box.send_keys(key)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)

        while True:
            try:
                job_cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.joblist-item'))
                )
            except:
                print("未找到职位数据")
                break

            random_scroll_and_wait(driver)

            for job in job_cards:
                try:
                    job_data = extract_job_data(job)
                    jobs_data.append(job_data)
                except Exception as e:
                    print(f"提取数据时出错，跳过该职位: {str(e)}")
                    continue

            try:
                current_page = driver.find_element(By.CSS_SELECTOR, ".el-pager .number.active").text
                print(f"当前页码：{current_page}")

                next_button = driver.find_element(By.CSS_SELECTOR, ".btn-next")
                previous_page = current_page

                next_button.click()
                time.sleep(3)

                new_page = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".el-pager .number.active"))
                ).text

                if new_page == previous_page:
                    print("已经是最后一页，程序结束。")
                    break

            except Exception as e:
                print(f"翻页时出错: {e}")
                break

    except Exception as e:
        print(f"爬取过程中发生错误: {str(e)}")

    return jobs_data

if __name__ == "__main__":
    while True:
        key = input("请输入要查找的关键词（0退出）:")
        if key == "0":
            break

        browser_name = input("请输入浏览器名称（Chrome/Edge/Firefox/Safari）：")
        try:
            driver = get_driver(browser_name)
            driver.maximize_window()
            print('----------------------------------\n----------------------------------')
            print("开始爬取数据，请稍候...")
            start_time = time.time()

            jobs = crawl(driver, key)

            if jobs:
                df = pd.DataFrame(jobs)
                filename = f"51_{key}岗位数据_{time.strftime('%Y%m%d%H%M%S')}.xlsx"
                df.to_excel(filename, index=False)
                print(f"成功保存 {len(jobs)} 条数据到 {filename}")
            else:
                print("未获取到任何数据，请检查关键词或网络状态。")
            print(f"总耗时: {time.time() - start_time:.2f}秒")
        except Exception as e:
            print(f"程序运行出错: {str(e)}")
        finally:
            driver.quit()