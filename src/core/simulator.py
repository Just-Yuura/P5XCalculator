from multiprocessing import Pool
from src.core.random_pool import RandomPool
from src.model.user_account import UserAccount
from src.model.enum.patch_type import PatchType
from src.model.enum.banner_type import BannerType
from src.model.enum.simulation_type import SimulationType

DEBUG_MODE = False
NUM_SIMULATIONS = 1 if DEBUG_MODE else 100_000

PATCH_DURATION_DAYS = 14

# Income Constants
MONTHLY_SUB_BONUS = 300
BP_JEWEL_BONUS = 650
BP_PLAT_TICKETS = 3
BP_PLAT_COINS = 7

SMALL_PATCH_JEWELS = 6000
BIG_PATCH_JEWELS = 10000

# Gacha Constants
CHAR_RATE_TARGETED = 0.004
CHAR_PITY_TARGETED = 110

CHAR_RATE_CHANCE = 0.008
CHAR_PITY_CHANCE = 80

WEAPON_RATE = 0.008
WEAPON_PITY = 70

CHAR_JEWEL_COST = 150
WEAPON_JEWEL_COST = 100


class Simulator:
    """
    Runs forecast simulations across potentially multiple patches based on user input.
    """

    def __init__(
            self,
            simulation_type,
            banner_type,
            current_jewels,
            plat_tickets,
            plat_coins,
            starting_pity_character,
            starting_pity_weapon,
            buy_bp,
            bp_days_left,
            buy_monthly_sub,
            sub_days_left,
            selected_banners
    ):
        """
        Initialize simulator with player resources and settings.

        :param simulation_type: SimulationType enum for luck modification
        :param banner_type: BannerType enum for picking between Chance(50/50) or Targeted banners
        :param current_jewels: Meta Jewels held by the player
        :param plat_tickets: Platinum Tickets held by the player
        :param plat_coins: Platinum Milicoins held by the player
        :param buy_bp: Boolean representation of whether the player purchases Phantom Passes
        :param bp_days_left: Days left on the currently running Phantom Pass
        :param buy_monthly_sub: Boolean representation of whether the player purchases monthly subscriptions
        :param sub_days_left: Days left on the currently running Subscription
        :param selected_banners: Dictionary of patch versions and their configs
        """
        self.random_pool = RandomPool()

        self.simulation_type = SimulationType(simulation_type)

        # Custom luck modifier for different scenarios based on users chosen simulation_type
        match self.simulation_type:
            case SimulationType.WORST_LUCK: # Always go full pity
                self.luck_mod = 0.0
            case SimulationType.BELOW_AVERAGE_LUCK: # Worse than Average luck for a slightly more pessimistic forecast
                self.luck_mod = 0.6
            case _:
                self.luck_mod = 1.0

        self.banner_type = BannerType(banner_type)

        self.patch_configs = selected_banners

        self.account = UserAccount(
            current_jewels,
            plat_tickets,
            plat_coins,
            starting_pity_character,
            starting_pity_weapon,
            buy_bp,
            bp_days_left,
            buy_monthly_sub,
            sub_days_left
        )


    def run_simulations(self):
        num_runs = 1 if self.simulation_type == SimulationType.WORST_LUCK else NUM_SIMULATIONS

        if num_runs != 1:
            with Pool() as pool:
                results = pool.starmap(self._run,
                                       [(self.account.clone(),) for _ in range(num_runs)])
        else:
            results = [self._run(self.account.clone()) for _ in range(num_runs)]

        return self._calculate_success_rate(results, num_runs)


    def _run(self, account):
        """
        Main simulation loop.

        Return:
            List of (obtained_chars, obtained_weapons, failure_info)
        """

        if not hasattr(self, "random_pool"):
            self.random_pool = RandomPool(buffer_size=10_000)

        patch_versions = list(self.patch_configs.keys())
        num_banners = len(patch_versions)

        obtained_chars = [False] * num_banners
        obtained_weapons = [False] * num_banners
        failures = []

        for idx, patch_version in enumerate(patch_versions):
            banner_config = self.patch_configs[patch_version]

            # Add income for patch period
            self._process_patch_income(account, idx, patch_version, patch_versions)

            # Attempt character pulls
            char_success = self._attempt_character_pulls(account, idx, banner_config, obtained_chars)

            if banner_config.get("pull_char", False) and not char_success:
                char_name = banner_config.get("featured_character", "")

                failures.append({
                    "patch": patch_version,
                    "failure_type": "character",
                    "featured_character": char_name
                })

            # If base char fails, skip rest
            if not char_success:
                continue

            weapon_success = self._attempt_weapon_pulls(account, idx, banner_config, obtained_weapons)

            if banner_config.get("pull_weapon", False) and not weapon_success:
                char_name = banner_config.get("featured_character", "")

                failures.append({
                    "patch": patch_version,
                    "failure_type": "weapon",
                    "featured_character": char_name
                })

            # If weapon was desired but not pulled, skip duplicates/refinements
            if not weapon_success and banner_config.get("pull_weapon", False):
                continue

            # Awareness & Refinement pulls
            awareness = banner_config.get("awareness", 0)
            duplicates_obtained = 0

            for dup_num in range(awareness):
                if self._pull_character(account):
                    duplicates_obtained += 1

                    if DEBUG_MODE:
                        print(f"Got character duplicate {dup_num + 1}/{awareness}!")
                else:
                    if DEBUG_MODE:
                        print(f"Ran out of jewels at duplicate {dup_num + 1}/{awareness}")
                    break

            refinement = banner_config.get("refinement", 0)
            refinements_obtained = 0

            for ref_num in range(refinement):
                if self._pull_weapon(account):
                    refinements_obtained += 1

                    if DEBUG_MODE:
                        print(f"Got weapon refinement {ref_num + 1}/{refinement}!")
                else:
                    if DEBUG_MODE:
                        print(f"Ran out of jewels at refinement {ref_num + 1}/{refinement}")
                    break

            # Mark as failed if didn't get all duplicates/refinements
            if duplicates_obtained < awareness:
                obtained_chars[idx] = False
                char_name = banner_config.get("featured_character", "")

                failures.append({
                    "patch": patch_version,
                    "failure_type": "awareness",
                    "featured_character": char_name,
                    "obtained": duplicates_obtained,
                    "needed": awareness
                })

            if weapon_success and refinements_obtained < refinement:
                obtained_weapons[idx] = False
                char_name = banner_config.get("featured_character", "")

                failures.append({
                    "patch": patch_version,
                    "failure_type": "refinement",
                    "featured_character": char_name,
                    "obtained": refinements_obtained,
                    "needed": refinement
                })

        return obtained_chars, obtained_weapons, failures


    def _add_income(self, account, from_patch, to_patch):
        """
        Process patch rewards, daily jewels and other forms of income within the period between two patches
        and adds them to the player's inventory.

        :param account: UserAccount to add income to
        :param from_patch: Starting patch version string
        :param to_patch: Ending patch version string
        """

        if from_patch == to_patch:
            return

        patch_versions = list(self.patch_configs.keys())

        try:
            from_idx = patch_versions.index(from_patch)
            to_idx = patch_versions.index(to_patch)
        except ValueError:
            return

        if to_idx <= from_idx:
            return

        num_patches = to_idx - from_idx

        # Add fixed jewel amount based on patch type
        for i in range(from_idx + 1, to_idx + 1):
            patch_version = patch_versions[i]
            patch_type = PatchType(self.patch_configs[patch_version]["patch_type"])

            if patch_type == PatchType.SMALL:
                account.add_jewels(SMALL_PATCH_JEWELS)
            elif patch_type == PatchType.BIG:
                account.add_jewels(BIG_PATCH_JEWELS)

        # Calculate daily jewel income, including handling for monthly sub
        total_days = num_patches * PATCH_DURATION_DAYS
        remaining_days = total_days

        while remaining_days > 0:
            if account.buy_sub:
                days_to_process = min(remaining_days, account.sub_days_left)
                account.add_jewels(days_to_process * account.daily_jewels)
                account.sub_days_left -= days_to_process
                remaining_days -= days_to_process

                if account.sub_days_left == 0:
                    account.add_jewels(MONTHLY_SUB_BONUS)
                    account.sub_days_left = 30
            else:
                # No monthly sub, use base daily jewel rate
                account.add_jewels(remaining_days * 60)
                remaining_days = 0

        # Process phantom pass rewards
        if account.buy_bp:
            days_to_process = total_days

            while days_to_process > 0:
                days_this_cycle = min(days_to_process, account.bp_days_left)
                account.bp_days_left -= days_this_cycle
                days_to_process -= days_this_cycle

                if account.bp_days_left == 0:
                    account.add_jewels(BP_JEWEL_BONUS)
                    account.add_tickets(BP_PLAT_TICKETS)
                    account.add_milicoins(BP_PLAT_COINS)
                    account.bp_days_left = 45


    def _pull_character(self, account):
        """
        Simulate character pulls until obtaining the desired character.

        Uses tickets first, converts violet conigems if needed, then spends jewels.

        :param account: UserAccount to pull from

        Returns:
            True if character obtained, False otherwise
        """
        if self.banner_type == BannerType.CHANCE: #Chance (50/50) Banner
            guaranteed_next = False

            while True:
                while True:
                    if not account.spend_ticket():
                        if account.current_jewels < CHAR_JEWEL_COST and account.violet_conigems >= 10:
                            account.convert_conigems()

                        if not account.spend_jewels(CHAR_JEWEL_COST):
                            return False

                    account.increment_character_pity()

                    if account.char_pulls_since_4star >= 10 and account.current_character_pity < CHAR_PITY_CHANCE:
                        account.reset_character_4star_counter()

                    if self.random_pool.get_single() < (CHAR_RATE_CHANCE * self.luck_mod) or account.current_character_pity >= CHAR_PITY_CHANCE:
                        account.reset_character_pity()

                        if guaranteed_next:
                            return True
                        else:
                            if self.random_pool.get_single() >= 0.5 or self.simulation_type == SimulationType.WORST_LUCK:
                                guaranteed_next = True
                                break
                            else:
                                return True

        else:  # Targeted (110 Pity) Banner
            while True:
                if not account.spend_ticket():
                    if account.current_jewels < CHAR_JEWEL_COST and account.violet_conigems >= 10:
                        account.convert_conigems()

                    if not account.spend_jewels(CHAR_JEWEL_COST):
                        return False

                account.increment_character_pity()

                if account.char_pulls_since_4star >= 10 and account.current_character_pity < CHAR_PITY_TARGETED:
                    account.reset_character_4star_counter()

                if self.random_pool.get_single() < (CHAR_RATE_TARGETED * self.luck_mod) or account.current_character_pity >= CHAR_PITY_TARGETED:
                    account.reset_character_pity()
                    return True


    def _pull_weapon(self, account):
        """
        Simulate weapon banner pulls.

        Uses coins first, converts violet conigems if needed, then spends jewels.

        :param account: UserAccount to pull from

        Returns:
            True if weapon obtained, False if insufficient resources
        """

        guaranteed_next = False

        while True:
            while True:
                if not account.spend_milicoin():
                    if account.current_jewels < WEAPON_JEWEL_COST and account.violet_conigems >= 10:
                        account.convert_conigems()

                    if not account.spend_jewels(WEAPON_JEWEL_COST):
                        return False

                account.increment_weapon_pity()

                if account.weapon_pulls_since_4star >= 10 and account.current_weapon_pity < WEAPON_PITY:
                    account.reset_weapon_4star_counter()

                if self.random_pool.get_single() < (WEAPON_RATE * self.luck_mod) or account.current_weapon_pity >= WEAPON_PITY:
                    account.reset_weapon_pity()

                    if guaranteed_next:
                        return True

                    # 50/50: Return True on win, go into the next pity cycle on loss
                    if self.random_pool.get_single() >= 0.5 or self.simulation_type == SimulationType.WORST_LUCK:
                        guaranteed_next = True
                        break
                    else:
                        return True


    def _process_patch_income(self, account, idx, patch_version, patch_versions):
        """
        Add income for this patch.

        :param account: UserAccount to process resources
        :param idx: Current patch index
        :param patch_version: Current patch version string
        :param patch_versions: List of all patch versions
        """
        if idx > 0 and idx < len(patch_versions) - 1:
            next_patch = patch_versions[idx + 1]
            self._add_income(account, patch_version, next_patch)

        if DEBUG_MODE:
            final_patch = " (Final Patch)" if idx == len(patch_versions) - 1 else ""
            print(f"\n=== Patch {patch_version}{final_patch} ===")
            print(f"Available jewels: {account.current_jewels:,}")
            print(f"Violet conigems: {account.violet_conigems}")
            print(f"Character pity: {account.current_character_pity}")
            print(f"Plat tickets: {account.owned_plat_tickets}")
            print(f"Plat coins: {account.owned_plat_coins}")


    def _attempt_character_pulls(self, account, idx, banner_config, obtained_chars):
        """
        Attempt to pull all needed characters from this banner.

        :param: account: UserAccount with which to perform the pulls
        :param idx: Current banner index
        :param banner_config: Configuration for this banner
        :param obtained_chars: List tracking which characters were obtained

        Returns:
            True if all characters obtained, False otherwise
        """
        pull_char = banner_config.get("pull_char", False)

        if not pull_char:
            return False

        awareness = banner_config.get("awareness", 0)
        chars_needed = awareness + 1
        chars_obtained = 0

        jewels_before = account.current_jewels
        tickets_before = account.owned_plat_tickets

        for char_num in range(chars_needed):
            char_success = self._pull_character(account)

            if char_success:
                chars_obtained += 1

                if DEBUG_MODE:
                    duplicate_text = f" (duplicate {char_num})" if char_num > 0 else ""
                    print(f"Got character{duplicate_text}!")
            else:
                if DEBUG_MODE:
                    duplicate_text = f" (duplicate {char_num})" if char_num > 0 else ""
                    print(f"Ran out of jewels while pulling character{duplicate_text}")
                break

        if chars_obtained == chars_needed:
            obtained_chars[idx] = True

            if DEBUG_MODE:
                jewels_spent = jewels_before - account.current_jewels
                tickets_used = tickets_before - account.owned_plat_tickets
                print(f"All {chars_needed} character(s) obtained! Used {tickets_used} tickets, {jewels_spent:,} jewels")
                print(f"Jewels remaining: {account.current_jewels:,}")

            return True
        else:
            if DEBUG_MODE:
                print(f"Only got {chars_obtained}/{chars_needed} characters")
                print(f"Pity carried forward: {account.current_character_pity}")
                print(f"Jewels remaining: {account.current_jewels:,}")

            return False


    def _attempt_weapon_pulls(self, account, idx, banner_config, obtained_weapons):
        """
        Attempt to pull the base weapon (no refinements).

        :param: account: UserAccount with which to perform the pulls
        :param idx: Current banner index
        :param banner_config: Configuration for this banner
        :param obtained_weapons: List tracking which weapons were obtained

        Returns:
            True if base weapon obtained, False otherwise
        """
        pull_weapon = banner_config.get("pull_weapon", False)

        if not pull_weapon:
            return False

        jewels_before = account.current_jewels
        coins_before = account.owned_plat_coins

        weap_success = self._pull_weapon(account)

        if weap_success:
            if DEBUG_MODE:
                jewels_spent = jewels_before - account.current_jewels
                coins_used = coins_before - account.owned_plat_coins
                print(f"Got base weapon! Used {coins_used} coins, {jewels_spent:,} jewels")
                print(f"Jewels remaining: {account.current_jewels:,}")

            obtained_weapons[idx] = True
            return True
        else:
            if DEBUG_MODE:
                print(f"Ran out of jewels while pulling base weapon")
                print(f"Jewels remaining: {account.current_jewels:,}")

            return False


    def _calculate_success_rate(self, results, num_runs):
        """
        Calculate the success rate across all simulation runs.

        :param results: List of (obtained_chars, obtained_weapons) tuples from simulations
        :param num_runs: Total number of simulation runs

        Returns:
            Dictionary with success_rate, successful_runs, and total_runs
        """
        successful_runs = 0
        failure_counts = {}

        for obtained_chars, obtained_weapons, failures in results:
            all_succeeded = True

            for idx, banner_config in enumerate(self.patch_configs.values()):
                if banner_config.get("pull_char", False):
                    if not obtained_chars[idx]:
                        all_succeeded = False
                        break

                if banner_config.get("pull_weapon", False):
                    if not obtained_weapons[idx]:
                        all_succeeded = False
                        break

            if all_succeeded:
                successful_runs += 1

            for failure in failures:
                key = (
                    failure["patch"],
                    failure["failure_type"],
                    failure.get("featured_character", "")
                )

                if key not in failure_counts:
                    failure_counts[key] = {
                        "count": 0,
                        "obtained_list": [],
                        "needed": failure.get("needed")
                    }

                failure_counts[key]["count"] += 1

                if "obtained" in failure and failure["obtained"] > 0:
                    failure_counts[key]["obtained_list"].append(failure["obtained"])

        success_rate = (successful_runs / num_runs) * 100 if num_runs > 0 else 0

        sorted_failures = sorted(
            failure_counts.items(),
            key=lambda x: (x[1]["count"], x[0][0], x[0][1]),
            reverse=True
        )

        return {
            "success_rate": success_rate,
            "successful_runs": successful_runs,
            "total_runs": num_runs,
            "failure_breakdown": sorted_failures
        }