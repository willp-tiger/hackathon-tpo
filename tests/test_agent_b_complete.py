from src.agents.strategist import CreativeCalendarAgent

if __name__ == "__main__":
    # Initialize agent
    agent = CreativeCalendarAgent()

    # Generate calendar
    calendar = agent.generate_calendar(
        causal_parameters_path="outputs/causal_parameters.json",
        budget_limit=1200000,
        display_config_path="case-data/Promo_config.csv",
        objective_prompt_path="case-data/objective_prompt.txt",
        output_path="outputs/draft_calendar_candidate.json"
    )

    print(f"\nGenerated {len(calendar['calendar_events'])} promotion events")
    print(f"Objective: {calendar['objective']}")
