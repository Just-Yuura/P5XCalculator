import copy

class UserAccount:
    """
    Manages players jewels, tickets, coins and pity counter
    """
    def __init__(
            self,
            current_jewels,
            plat_tickets,
            plat_coins,
            starting_pity_character,
            starting_pity_weapon,
            buy_bp,
            bp_days_left,
            buy_monthly_sub,
            sub_days_left
    ):
        """
        Initialize user account with provided inputs.

        :param current_jewels: Meta Jewels held by the player
        :param plat_tickets: Platinum Tickets held by the player
        :param plat_coins: Platinum Milicoins held by the player
        :param buy_bp: Whether the player purchases Phantom Passes
        :param bp_days_left: Days left on the currently running Phantom Pass
        :param buy_monthly_sub: Whether the player purchases monthly subscriptions
        :param sub_days_left: Days left on the currently running subscription
        """

        # Currency
        self.current_jewels = int(current_jewels)
        self.owned_plat_tickets = int(plat_tickets)
        self.owned_plat_coins = int(plat_coins)
        self.violet_conigems = 0

        # Pity counters
        self.current_character_pity = int(starting_pity_character)
        self.current_weapon_pity = int(starting_pity_weapon)
        self.char_pulls_since_4star = 0
        self.weapon_pulls_since_4star = 0

        # Subscription/Phantom Pass tracking
        self.buy_bp = buy_bp
        self.bp_days_left = int(bp_days_left)
        self.buy_sub = buy_monthly_sub
        self.sub_days_left = int(sub_days_left)
        self.daily_jewels = 160 if buy_monthly_sub else 60


    def add_jewels(self, amount):
        """
        Adds amount of jewels to the account.
        """
        self.current_jewels += amount


    def add_tickets(self, amount):
        """
        Adds amount of platinum tickets to the account.
        """
        self.owned_plat_tickets += amount


    def add_milicoins(self, amount):
        """
        Adds amount of platinum milicoins to the account
        """
        self.owned_plat_coins += amount


    def add_conigems(self, amount):
        """
        Adds amount of violet conigems to the account
        """
        self.violet_conigems += amount


    def spend_jewels(self, amount):
        """
        Attempt to spend Meta Jewels.
        :param amount: Amount of Meta Jewels to spend.

        Returns:
            False if owned meta jewels are insufficient, True otherwise.
        """

        if self.current_jewels >= amount:
            self.current_jewels -= amount

            return True
        else:
            return False


    def spend_ticket(self):
        """
        Attempt to spend a platinum ticket.

        Return:
            False if no tickets available, True otherwise.
        """

        if self.owned_plat_tickets > 0:
            self.owned_plat_tickets -= 1

            return True
        else:
            return False


    def spend_milicoin(self):
        """
        Attempt to spend a platinum milicoin.

        Return:
            False if no coins available, True otherwise.
        """

        if self.owned_plat_coins > 0:
            self.owned_plat_coins -= 1

            return True
        else:
            return False


    def convert_conigems(self):
        """
        Convert all currently owned violet onigems to meta jewels

        Returns:
            Number of conversions performed
        """

        if self.violet_conigems >= 10:
            conversions = self.violet_conigems // 10
            self.current_jewels += conversions * 100
            self.violet_conigems -= conversions * 10

            return conversions

        return 0


    def increment_character_pity(self):
        self.current_character_pity += 1
        self.char_pulls_since_4star += 1


    def reset_character_pity(self):
        self.current_character_pity = 0


    def reset_character_4star_counter(self):
        self.add_conigems(10)
        self.char_pulls_since_4star = 0


    def increment_weapon_pity(self):
        self.current_weapon_pity += 1
        self.weapon_pulls_since_4star += 1


    def reset_weapon_pity(self):
        self.current_weapon_pity = 0


    def reset_weapon_4star_counter(self):
        self.add_conigems(10)
        self.weapon_pulls_since_4star = 0


    def clone(self):
        return copy.copy(self)