from bs4 import BeautifulSoup
import requests 


new_url = "https://store.steampowered.com/explore/new/"


class Game:
    def __init__(self, id, name, price, discount):
        self.id = id
        self.name = name
        self.price = price
        self.discount = discount

class MonthTopSellers:
    def __init__(self, games, image_name):
        self.games = games
        self.image_name = image_name
    

def get_price(game_div):
    children_num = len(list(game_div.find_all(recursive=False)))
    #print("Children Num:", children_num)
    price_div = game_div.find_all("div", recursive=False)[children_num - 1]
    #print(price_div.prettify())
    price = price_div.find(class_="discount_final_price").contents[0]
    return price[:-1].replace(",", ".")

def get_discount(game_div, price):
    original_price_div = game_div.find(class_="discount_original_price")
    
    if original_price_div:
        og_price = original_price_div.contents[0][:-1].replace(",", ".")
    else:
        og_price = price

    og_price = float(og_price)
    price = float(price)
    return int((og_price - price) / og_price * 100)

def get_image(name, game_div):
    img_url = game_div.find(class_="capsule headerv5").find("img")["src"]
    url_parts = img_url.split("?")[0].split("header_")
    part1 = url_parts[0] + "header"
    img_type = url_parts[1].split(".")[1]
    part2 = "." + img_type
    img_url_final = part1 + part2
    print("Header URL:", img_url_final)

    img_data = requests.get(img_url_final).content
    folder_name = "../header_images"
    img_name = name + "_header." + img_type
    path = folder_name + "/" + img_name

    with open(path, 'wb') as handler:
        handler.write(img_data)

    return img_name

def get_month_top_sellers():
    new_html = requests.get(new_url).text
    soup = BeautifulSoup(new_html, 'html.parser')
    month_top_div = soup.find(class_="peeking_carousel store_horizontal_autoslider store_capsule_container_scrolling bucket_contents")
    games_as = month_top_div.find_all("a" , recursive=False) 
    count = 0 # total = 10
    games = []

    for game_div in games_as:
        #print(game_div.prettify() + "\n\n------------------\n\n")

        id = game_div["data-ds-appid"]
        print("Id:", id)

        name = game_div.find(class_="capsule headerv5").find("img")["alt"]
        print("Name:", name)

        price = get_price(game_div)
        print("Price:", price)

        discount = get_discount(game_div, price)
        print("Discount:", discount)

        games.append(Game(id, name, price, discount))

        if count == 0:
            img_name = get_image(name, game_div)

        count += 1
        print()
    
    return MonthTopSellers(games, img_name)
