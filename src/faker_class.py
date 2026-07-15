# Built-in Python library
# Used to generate random numbers
import random


# Third-party libraries

# Used to read YAML configuration files
import yaml

# Library for generating fake data
# Examples:
# - fake names
# - emails
# - addresses
# - dates
from faker import Faker


# Project logger
from src.logger import Logger



class FakerWrapper:
    """
    Wrapper class around Faker library.

    Responsibility:
    - Load fake data generation rules from YAML file
    - Create Faker instance
    - Generate fake documents based on mapping configuration


    This class separates data generation logic from the main application.

    Instead of writing:

        fake.name()
        fake.email()
        fake.address()

    everywhere, we define rules in faker_mappings.yml
    and this class generates documents dynamically.
    """


    def __init__(self):
        """
        Constructor method.

        When this class is initialized:
        1. Create logger
        2. Load faker mapping configuration
        3. Initialize Faker library
        """


        # Create logger instance for this class
        self.logger = Logger(__name__)



        # Load fake data generation rules from YAML file
        #
        # File:
        # data/faker_mappings.yml
        #
        # Example content:
        #
        # mappings:
        #   title:
        #       faker: sentence
        #
        #   email:
        #       faker: email
        #
        #   rating:
        #       faker: uniform
        #       kwargs:
        #           min_value: 0
        #           max_value: 10
        #
        #
        # The YAML file controls:
        # - Which fields should exist
        # - Which Faker provider should generate them
        # - What arguments should be passed


        with open(
            'data/faker_mappings.yml',
            'r'
        ) as f:


            # Convert YAML content into Python dictionary
            #
            # Example:
            #
            # YAML:
            # faker: email
            #
            # becomes:
            #
            # {
            #    "faker":"email"
            # }
            #
            #
            # We only extract the "mappings" section
            self.mapping = yaml.safe_load(f)['mappings']



        # Initialize Faker object
        #
        # This object provides fake data generators:
        #
        # fake.name()
        # fake.email()
        # fake.address()
        #
        self.fake = Faker()



        self.logger.info(
            "Initialize FakerWrapper Class"
        )



    def generate_data(
            self,
            mapping=None,
            num_documents=1
    ) -> list:
        """
        Generate fake documents based on mapping configuration.


        Args:

            mapping:
                Dictionary describing how each field should be generated.

                If no mapping is provided,
                self.mapping loaded from YAML will be used.


            num_documents:
                Number of fake documents to generate.


        Returns:

            Generator that yields fake documents one by one.


        Example output:

        {
            "title": "The Matrix",
            "email": "test@gmail.com",
            "rating": 8.5
        }


        Note:
        This function uses yield, therefore it is a generator.

        It does not create all documents in memory.
        It generates documents when requested.
        """



        # If no custom mapping is provided,
        # use mapping loaded from faker_mappings.yml
        if mapping is None:
            mapping = self.mapping



        # Generate requested number of documents
        for i in range(num_documents):


            # Each loop creates one Elasticsearch document
            #
            # Example:
            #
            # {
            #    "title":"Batman",
            #    "genre":"Action"
            # }
            document = {}



            # Iterate through every field defined in mapping
            #
            # Example mapping:
            #
            # {
            #    "title":{
            #        "faker":"sentence"
            #    },
            #
            #    "rating":{
            #        "faker":"uniform"
            #    }
            # }
            #
            for field, value in mapping.items():



                # Special case:
                #
                # "uniform" is not a Faker provider.
                #
                # It means:
                # Generate a random number between min and max.
                #
                # Example:
                #
                # rating:
                #   faker: uniform
                #   kwargs:
                #       min_value: 1
                #       max_value: 10

                if value['faker'] == 'uniform':



                    # Get extra arguments from mapping
                    #
                    # Example:
                    #
                    # {
                    #   min_value:1,
                    #   max_value:10
                    # }
                    kwargs = value.get(
                        'kwargs',
                        {}
                    )



                    # Default minimum value
                    # Used if min_value is not provided
                    min_value = kwargs.get(
                        'min_value',
                        0
                    )


                    # Default maximum value
                    # Used if max_value is not provided
                    max_value = kwargs.get(
                        'max_value',
                        1
                    )



                    # Generate random float number
                    #
                    # Example:
                    #
                    # random.uniform(1,10)
                    #
                    # Result:
                    # 7.42
                    #
                    # round(...,2)
                    # keeps only 2 decimal places

                    document[field] = round(
                        random.uniform(
                            min_value,
                            max_value
                        ),
                        2
                    )



                else:

                    # For normal Faker providers:
                    #
                    # Example:
                    #
                    # faker: email
                    #
                    # becomes:
                    #
                    # self.fake.email()
                    #
                    faker_method = value.get(
                        'faker'
                    )



                    # Get arguments for Faker provider
                    #
                    # Example:
                    #
                    # faker: sentence
                    # kwargs:
                    #    nb_words: 5
                    #
                    # becomes:
                    #
                    # fake.sentence(nb_words=5)

                    kwargs = value.get(
                        'kwargs',
                        {}
                    )



                    # Dynamically call Faker method
                    #
                    # getattr allows calling a method
                    # by its name stored as string.
                    #
                    # Example:
                    #
                    # faker_method = "email"
                    #
                    # getattr(self.fake,"email")
                    #
                    # becomes:
                    #
                    # self.fake.email()
                    #
                    document[field] = getattr(
                        self.fake,
                        faker_method
                    )(
                        **kwargs
                    )



            # Return one generated document
            #
            # Because we use yield:
            #
            # document1
            # document2
            # document3
            #
            # are generated only when requested.
            #
            # This is memory efficient for millions of documents.

            yield document