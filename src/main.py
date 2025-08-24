from steam_info import get_month_top_sellers
from x_bot import XBot


def main():
    xbot = XBot()
    month_top_sellers = get_month_top_sellers()
    tweet_text = ""
    # format text
    # xbot.tweet()


if __name__ == "__main__":
    main()
