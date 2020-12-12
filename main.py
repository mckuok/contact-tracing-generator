import csv
import random
from enum import Enum


class Location(Enum):
    LIVING_ROOM = 1
    RESTAURANT_TABLE = 2
    INDOOR_PARTY = 3
    CONFERENCE_ROOM = 4
    CLASSROOM = 5
    OUTDOOR_HIKE = 6


class InfectionProbabilitiesMapper:

    @staticmethod
    def get_infection_probability(location, infected_count, wearing_mask, social_distancing):
        """
        Calculates the probability of infection based on the properties
        :param location: the location profile
        :param infected_count: the number of infected population in the same location
        :param wearing_mask: if the person is wearing mask
        :param social_distancing: if the person is social distancing
        :return:
        """
        location = location.location

        if infected_count == 0 or location is Location.OUTDOOR_HIKE:
            return 0

        if location is Location.OUTDOOR_HIKE:
            return 0.01

        if location is Location.LIVING_ROOM:
            location_prob = 0.4

        if location is Location.RESTAURANT_TABLE:
            location_prob = 0.3

        if location is Location.INDOOR_PARTY:
            location_prob = 0.25

        if location is Location.CONFERENCE_ROOM:
            location_prob = 0.2

        if location is Location.CLASSROOM:
            location_prob = 0.15

        if wearing_mask:
            infected_mask_prob = 0.03
        else:
            infected_mask_prob = 0.9

        if social_distancing:
            infected_social_distancing_prob = 0.05
        else:
            infected_social_distancing_prob = 0.7

        return (0.5 * location_prob + 0.3 * infected_mask_prob + 0.2 * infected_social_distancing_prob) * \
               (1 + min(10, infected_count) / 10 * 0.5) / 4


class PersonDay:

    def __init__(self, day, person, place, pre_visit_covid, post_visit_covid, mask, social_distancing):
        self.day = day
        self.person = person
        self.place = place
        self.pre_visit_covid = pre_visit_covid
        self.post_visit_covid = post_visit_covid
        self.mask = mask
        self.social_distancing = social_distancing

    def to_csv_row(self):
        """
        Converts the day into a csv row
        :return: a list representation of a row in the result csv
        """
        person_name = "person " + str(self.person.id)
        location_name = self.place.location.name.lower() + " " + str(self.place.id)
        return [self.day, person_name, location_name, str(self.pre_visit_covid),
                str(self.post_visit_covid), str(self.mask), str(self.social_distancing)]


class PersonProfile:
    HIGH_MASK_WEARING_PROBABILITY = 0.7
    HIGH_SOCIAL_DISTANCING_PROBABILITY = 0.6

    LOW_MASK_WEARING_PROBABILITY = 0.2
    LOW_SOCIAL_DISTANCING_PROBABILITY = 0.1

    def __init__(self, _id, likely_wear_mask, likely_social_distancing):
        self.id = _id
        self.mask_prob = PersonProfile.HIGH_MASK_WEARING_PROBABILITY if likely_wear_mask else \
            PersonProfile.LOW_MASK_WEARING_PROBABILITY
        self.social_distancing_prob = PersonProfile.HIGH_SOCIAL_DISTANCING_PROBABILITY if likely_social_distancing else \
            PersonProfile.LOW_SOCIAL_DISTANCING_PROBABILITY

    def will_wear_mask(self):
        """
        :return: true if the person will wear mask based on probability, false otherwise
        """
        return random.random() < self.mask_prob

    def will_social_distance(self):
        """
        :return: true if the person will social distance based on probability, false otherwise
        """
        return random.random() < self.social_distancing_prob

    def __eq__(self, other):
        return other.id == self.id

    def __hash__(self):
        return hash(self.id)


class LocationProfile:

    def __init__(self, _id, location):
        self.id = _id
        self.location = location


class PeopleTracker:

    def __init__(self, population_count, initial_infection_rate, mask_wearing_rate, social_distancing_rate):
        self.simulated_day = 0
        self.population = self.generate_population(population_count, mask_wearing_rate, social_distancing_rate)
        self.available_locations = self.generate_available_locations()
        self.infected_population = set(self.get_initial_infected_population(initial_infection_rate))

    def get_initial_infected_population(self, initial_infection_rate):
        """
        :param initial_infection_rate: the initial infection rate in decimal
        :return: the list of infected population
        """
        initial_infected_population = int(len(self.population) * initial_infection_rate)
        return random.sample(self.population, initial_infected_population)

    @staticmethod
    def generate_population(population_count, mask_wearing_rate, social_distancing_rate):
        """
        :param population_count: the number of total population
        :param mask_wearing_rate: the rate of people that wear mask
        :param social_distancing_rate: the rate of people that social distance
        :return: the list of person profiles
        """
        population = []
        for i in range(population_count):
            likely_wear_mask = random.random() < mask_wearing_rate
            likely_social_distancing = random.random() < social_distancing_rate
            population.append(PersonProfile(i, likely_wear_mask, likely_social_distancing))

        return population

    @staticmethod
    def generate_available_locations():
        """
        Generates a list of available locations. Each l
        :return:
        """
        available_locations = []
        all_locations = list(Location)
        for location in all_locations:
            location_count = random.randint(1, 5)
            for i in range(location_count):
                available_locations.append(LocationProfile(i, location))
        return available_locations

    def simulate_day(self):
        """
        Makes a simulation of the day
        :return: a summary of the day that details out the location each person in the population visited
        """
        # who goes to where
        location_assignment, grouped_location = self.determine_locations()

        # update infection
        summary = self.update_infection(grouped_location)
        self.simulated_day += 1

        return summary

    def determine_locations(self):
        """
        Determines the location each person has visited
        :return: a tuple of dictionaries. One keyed by location, one keyed by the person
        """
        location_assignment = {}
        grouped_location = {}
        for person in self.population:
            location = random.choice(self.available_locations)
            location_assignment[person] = location
            grouped_location.setdefault(location, []).append(person)

        return location_assignment, grouped_location

    def update_infection(self, group_by_locations):
        """
        Updates the infection for each person based on where they have visited
        :param group_by_locations: a dictionary keyed by location
        :return: a summary of the day that details out the location each person in the population visited
        """
        day_summary = []
        for location in group_by_locations:
            people_in_location = group_by_locations[location]

            infected_count_in_location = 0
            for person in people_in_location:
                if person in self.infected_population:
                    infected_count_in_location += 1

            for person in people_in_location:
                wore_mask = person.will_wear_mask()
                social_distanced = person.will_social_distance()
                if infected_count_in_location == 0 and person not in self.infected_population:
                    pre_covid = False
                    post_covid = False
                elif person in self.infected_population:
                    pre_covid = True
                    post_covid = True
                else:
                    pre_covid = False
                    infection_probability = InfectionProbabilitiesMapper.get_infection_probability(
                        location, infected_count_in_location, wore_mask, social_distanced)

                    post_covid = random.random() < infection_probability

                if post_covid:
                    self.infected_population.add(person)

                day_summary.append(PersonDay(self.simulated_day, person, location, pre_covid, post_covid, wore_mask,
                                             social_distanced))

        day_summary.sort(
            key=lambda people_day: (people_day.place.location.value, people_day.place.id, people_day.person.id))
        return day_summary


class CovidDataGenerator:
    POPULATION = 1500
    INITIAL_INFECTION_RATE = 0.03
    TIME_LENGTH = 7
    MASK_WEARING_RATE = 0.7
    SOCIAL_DISTANCING_RATE = 0.5

    def __init__(self):
        self.people_tracker = PeopleTracker(CovidDataGenerator.POPULATION, CovidDataGenerator.INITIAL_INFECTION_RATE,
                                            CovidDataGenerator.MASK_WEARING_RATE,
                                            CovidDataGenerator.SOCIAL_DISTANCING_RATE)

    def generate_csv(self, csv_file):
        """
        Generates the covid contact tracing data to the csv file
        :param csv_file: the name of the csv file that write to
        """
        with open(csv_file, 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(['day', 'person', 'place', 'pre-visit covid positive', 'post-visit covid positive',
                             'mask', 'social distancing'])
            for i in range(CovidDataGenerator.TIME_LENGTH):
                for row in self.generate_data():
                    writer.writerow(row.to_csv_row())

    def generate_data(self):
        """
        Generates data for that contains each person's day
        :rtype: list
        """
        people_data = self.people_tracker.simulate_day()
        for person in people_data:
            yield person


if __name__ == '__main__':
    generator = CovidDataGenerator()
    generator.generate_csv("contact_tracing.csv")
